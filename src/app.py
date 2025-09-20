from flask import Flask, render_template, request, Response

import youtube_utils as yt
import tasks

app = Flask(__name__)


@app.route('/')
def index():
    url = request.args.get('url')
    if url is not None:
        video_data = yt.get_video_data(url)
    else:
        video_data = None

    return render_template('index.html', video=video_data)


@app.route('/download/')
def start_download():
    url = request.args.get('url')
    video_stream_id = request.args.get('video-stream-id')
    audio_stream_id = request.args.get('audio-stream-id')

    task = tasks.download_stream.delay(url, video_stream_id, audio_stream_id)

    return {'taskId': task.id}


@app.route('/download/<task_id>/status')
def get_download_status(task_id):
    status = tasks.get_download_status(task_id)

    return status


@app.route('/download/<task_id>')
def download_file(task_id):
    filename = tasks.get_filename(task_id)

    response = Response()

    redirect_path = f'/media/{filename}'
    response.headers['X-Accel-Redirect'] = redirect_path

    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'

    del response.headers['Content-Type']

    return response