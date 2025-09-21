import yt_dlp
import os.path

TEMP_FOLDER = 'media'
USER_FILENAME_TEMPLATE = '%(title)s.%(ext)s'
STORAGE_FILENAME_TEMPLATE = '%(id)s-%(format_id)s.%(ext)s'
OUTPUT_TEMPLATE = os.path.join(TEMP_FOLDER, STORAGE_FILENAME_TEMPLATE)
STANDARD_FORMAT_NOTES = {'none', 'low', 'medium', 'high'}


def fetch_metadata(video_url):
    ydl_options = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info


def pair_audio_streams(video_streams, audio_streams):
    previous_resolution = ''
    max_audio_abr = False
    audio_stream_index = -1
    for video_stream in video_streams[1:]:
        current_resolution = video_stream['resolution']
        if not max_audio_abr and current_resolution != previous_resolution:
            previous_resolution = current_resolution
            audio_stream_index += 1
            if audio_stream_index == len(audio_streams) - 1:
                max_audio_abr = True

        for audio_stream in audio_streams[audio_stream_index::-1]:
            if audio_stream['ext'] != 'm4a' or video_stream['ext'] != 'webm':
                video_stream['audio_stream_id'] = audio_stream['id']
                video_stream['filesize'] += audio_stream['filesize']
                break

    return video_streams


def filter_and_format_streams(metadata):
    audio_streams = []
    video_streams = []

    for stream in metadata['formats']:
        if stream.get('vcodec') != 'none' and stream.get('acodec') == 'none':
            if 'avc' in stream['vcodec']:
                continue

            stream_info = {
                'id': stream.get('format_id'),
                'ext': stream.get('ext'),
                'filesize': stream.get('filesize', 0),
                'resolution': int(stream.get('resolution', '0x0').split('x')[1]),
                'fps': int(stream.get('fps'))
            }
            video_streams.append(stream_info)

        elif stream.get('acodec') != 'none' and stream.get('vcodec') == 'none':
            if stream['format_id'].endswith('-drc'):
                continue

            format_note = stream.get('format_note', 'none')

            if format_note not in STANDARD_FORMAT_NOTES and 'original' not in format_note:
                continue

            stream_info = {
                'id': stream['format_id'],
                'ext': stream.get('ext'),
                'filesize': stream.get('filesize', 0),
                'abr': round(stream.get('abr'))
            }
            audio_streams.append(stream_info)

    video_streams.sort(key=lambda s: s['resolution'])
    audio_streams.sort(key=lambda s: s['abr'])

    video_streams = pair_audio_streams(video_streams, audio_streams)

    return {'video': video_streams, 'audio': audio_streams}


def get_video_data(video_url):
    metadata = fetch_metadata(video_url)

    streams = filter_and_format_streams(metadata)

    video_data = {
        'url': video_url,
        'title': metadata.get('title'),
        'thumbnail_url': metadata.get('thumbnail'),
        'streams': streams
    }

    return video_data


def download_stream(url, video_stream_id, audio_stream_id, progress_callback):
    if video_stream_id and audio_stream_id:
        format_string = f'{video_stream_id}+{audio_stream_id}'
    else:
        format_string = audio_stream_id or video_stream_id

    total_downloaded_bytes = 0

    ydl_options = {
        'format': format_string,
        'outtmpl': OUTPUT_TEMPLATE,
        'quiet': True,
        'noprogress': True
    }

    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(url, download=False)
        storage_filepath = f'/{ydl.prepare_filename(info)}'
        user_filename = ydl.prepare_filename(info, outtmpl=USER_FILENAME_TEMPLATE)
        filesize_bytes = sum(stream['filesize'] for stream in info['requested_formats'])

        def progress_hook(d):
            nonlocal total_downloaded_bytes
            status = d['status']
            if status == 'finished':
                total_downloaded_bytes += d['downloaded_bytes']
            else:
                download_percentage = ((total_downloaded_bytes + d['downloaded_bytes']) / filesize_bytes) * 100
                progress_callback(round(download_percentage, 2))

        ydl.add_progress_hook(progress_hook)
        ydl.process_info(info)

    return storage_filepath, user_filename