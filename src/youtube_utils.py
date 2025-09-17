import yt_dlp
import os.path

TEMP_FOLDER = 'temp'
OUTPUT_TEMPLATE = os.path.join(TEMP_FOLDER, '%(title)s.%(ext)s')


def fetch_metadata(video_url):
    ydl_opts = {'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            return info
        except yt_dlp.DownloadError as e:
            print(f"Error fetching video info: {e}")
            return None


def extract_title_and_thumbnail(metadata):
    if not metadata:
        return None, None

    title = metadata.get('title')
    thumbnail_url = metadata.get('thumbnail')

    return title, thumbnail_url


def filter_and_format_streams(metadata):
    if not metadata or 'formats' not in metadata:
        return {}

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

            stream_info = {
                'id': stream['format_id'],
                'ext': stream.get('ext'),
                'filesize': stream.get('filesize', 0),
                'abr': round(stream.get('abr'))
            }
            audio_streams.append(stream_info)

    video_streams.sort(key=lambda s: s['resolution'], reverse=True)
    audio_streams.sort(key=lambda s: s['abr'], reverse=True)

    quality_threshold = len(video_streams) - len(audio_streams)
    for index, stream in enumerate(video_streams, 1):
        if index <= quality_threshold:
            audio_stream = audio_streams[0]
        else:
            audio_stream = audio_streams[min(index - quality_threshold, len(audio_streams)-1)]

        stream['audio_stream_id'] = audio_stream['id']
        stream['filesize'] += audio_stream['filesize']

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


def get_download_info(url, video_stream_id, audio_stream_id):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)

        total_download_size = 0
        for stream in info['formats']:
            if stream['format_id'] == video_stream_id:
                video_ext = stream['ext']
                total_download_size += stream.get('filesize', 0)
            elif stream['format_id'] == audio_stream_id:
                audio_ext = stream['ext']
                total_download_size += stream.get('filesize', 0)

        if video_stream_id:
            info['ext'] = video_ext
        else:
            info['ext'] = audio_ext

        filename = ydl.prepare_filename(info, outtmpl=OUTPUT_TEMPLATE)

        return filename, total_download_size, info['ext']


def download_stream(url, video_stream_id, audio_stream_id, progress_hook, extension):
    if video_stream_id and audio_stream_id:
        format_string = f'{video_stream_id}+{audio_stream_id}'
    else:
        format_string = audio_stream_id if audio_stream_id is not None else video_stream_id

    ydl_options = {
        'format': format_string,
        'outtmpl': OUTPUT_TEMPLATE,
        'quiet': True,
        'progress_hooks': [progress_hook],
        'merge_output_format': extension
    }

    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        ydl.download([url])