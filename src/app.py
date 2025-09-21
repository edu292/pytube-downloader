from flask import Flask, render_template, request, Response
from unidecode import unidecode
from urllib.parse import quote
import json

import youtube_utils as yt
import tasks

app = Flask(__name__)


def generate_sse_events(update_stream):
    for update in update_stream:
        data = json.dumps(update)
        yield f'data: {data}\n\n'



@app.route('/')
def index():
    url = request.args.get('url')
    if url is not None:
        video_data = yt.get_video_data(url)
    else:
        video_data = None

    return render_template('index.html', video=video_data)


@app.route('/download/', methods=['POST'])
def start_download():
    data = request.get_json()
    url = data.get('url')
    video_stream_id = data.get('videoStreamId')
    audio_stream_id = data.get('audioStreamId')

    if not url or not audio_stream_id:
        return {'error', 'Missing required attribute'}, 400

    task = tasks.download_stream.delay(data['url'], video_stream_id, audio_stream_id)

    return {'taskId': task.id}


@app.route('/download/<task_id>/status-stream')
def stream_download_status(task_id):
    task_updates = tasks.stream_task_updates(task_id)
    sse_events_stream = generate_sse_events(task_updates)

    return Response(sse_events_stream, mimetype='text/event-stream')


@app.route('/download/<task_id>')
def download_file(task_id):
    download_details = tasks.get_download_details(task_id)
    user_filename = download_details['user_filename']
    ascii_filename = unidecode(user_filename)
    encoded_filename = quote(user_filename)

    response = Response()
    response.headers['X-Accel-Redirect'] = download_details['storage_filepath']
    response.headers['Content-Disposition'] = (
        f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
    )
    del response.headers['Content-Type']

    return response