from urllib.parse import quote

import unicodedata
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


@app.route('/download/<task_id>/status-stream')
def get_download_status_stream(task_id):
    return Response(tasks.get_task_status_stream(task_id), mimetype='text/event-stream')


@app.route('/download/<task_id>')
def download_file(task_id):
    download_details = tasks.get_download_details(task_id)

    user_filename = download_details['user_filename']

    nfkd_form = unicodedata.normalize('NFKD', user_filename)
    ascii_filename = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    encoded_filename = quote(user_filename)

    response = Response()
    response.headers['X-Accel-Redirect'] = download_details['storage_filepath']

    response.headers['Content-Disposition'] = (
        f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    )

    del response.headers['Content-Type']

    return response