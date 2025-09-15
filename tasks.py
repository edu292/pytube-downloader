from celery import Celery
from celery.result import AsyncResult
import youtube_utils as yt

app = Celery('youtube-downloader',
             broker_url='redis://localhost:6379/0',
             backend='redis://localhost:6379/1')


@app.task(bind=True)
def download_stream(self, url, video_stream_id, audio_stream_id):
    filepath, filesize_bytes, extension = yt.get_download_info(url, video_stream_id, audio_stream_id)
    total_downloaded_bytes = 0

    def progress_hook(d):
        status = d['status']
        nonlocal total_downloaded_bytes
        if status == 'finished':
            total_downloaded_bytes += d['downloaded_bytes']

        else:
            self.update_state(
                state='DOWNLOADING',
                meta={
                    'percentage': ((total_downloaded_bytes + d['downloaded_bytes']) / filesize_bytes) * 100
                }
            )

    yt.download_stream(url, video_stream_id, audio_stream_id, progress_hook, extension)

    return filepath


def get_download_status(task_id):
    task = AsyncResult(task_id, app=app)

    response_data = {
        'state': task.state,
        'percentage': 0
    }

    if task.info and isinstance(task.info, dict):
        response_data.update({
            'percentage': task.info.get('percentage', 0)
        })

    return response_data


def get_filepath(task_id):
    task = AsyncResult(task_id, app=app)

    return task.result