from time import sleep

from celery import Celery
from celery.result import AsyncResult
import youtube_utils as yt

app = Celery('youtube-downloader',
             broker_url='redis://redis:6379/0',
             backend='redis://redis:6379/1')


@app.task(bind=True)
def download_stream(self, url, video_stream_id, audio_stream_id):
    def progress_hook(percentage):
        self.update_state(
            state='PROGRESS',
            meta={'percentage': percentage}
        )

    storage_filepath, user_filename = yt.download_stream(url, video_stream_id, audio_stream_id, progress_hook)

    return {'storage_filepath': storage_filepath, 'user_filename': user_filename}


def stream_task_updates(task_id):
    task = AsyncResult(task_id, app=app)
    last_percentage = -1

    while not task.ready():
        if task.state == 'PROGRESS':
            percentage = task.info['percentage']

        elif task.state == 'PENDING':
            percentage = 0

        if percentage != last_percentage:
            yield {'state': task.state,'percentage': percentage}
            last_percentage = percentage

        sleep(1)

    final_percentage = 100 if task.state == 'SUCCESS' else last_percentage
    yield {'state': task.state, 'percentage': final_percentage}


def get_download_details(task_id):
    task = AsyncResult(task_id, app=app)

    return task.result