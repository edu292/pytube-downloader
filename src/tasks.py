from time import sleep

from celery import Celery
from celery.result import AsyncResult
import youtube_utils as yt
import json

app = Celery('youtube-downloader',
             broker_url='redis://redis:6379/0',
             backend='redis://redis:6379/1')


def _format_sse_event(data):
    return f'data: {json.dumps(data)}\n\n'


@app.task(bind=True)
def download_stream(self, url, video_stream_id, audio_stream_id):
    def progress_hook(percentage):
        self.update_state(
            state='DOWNLOADING',
            meta={'percentage': percentage}
        )

    storage_filepath, user_filename = yt.download_stream(url, video_stream_id, audio_stream_id, progress_hook)

    return {'storage_filepath': storage_filepath, 'user_filename': user_filename}


def get_task_status_stream(task_id):
    task = AsyncResult(task_id, app=app)
    last_percentage = -1

    initial_event = {'state':task.state, 'percentage': 0}
    yield _format_sse_event(initial_event)

    while not task.ready():
        if task.info and isinstance(task.info, dict):
            percentage = task.info.get('percentage', 0)
            if percentage != last_percentage:
                event_data = {
                    'state': task.state,
                    'percentage': percentage
                }
                yield _format_sse_event(event_data)
                last_percentage = percentage

        sleep(0.5)

    last_event = {'state': task.state, 'percentage': 100}
    yield _format_sse_event(last_event)


def get_download_details(task_id):
    task = AsyncResult(task_id, app=app)

    return task.result