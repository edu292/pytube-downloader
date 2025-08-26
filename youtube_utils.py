import yt_dlp
import subprocess


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

    audio_streams = {}
    video_streams = {}

    for stream in metadata['formats']:
        if stream.get('vcodec') != 'none' and stream.get('acodec') == 'none':
            if 'avc' in stream['vcodec']:
                continue

            video_streams[stream['format_id']] = {
                'id': stream.get('format_id'),
                'ext': stream.get('ext'),
                'filesize': stream.get('filesize', 0),
                'resolution': int(stream.get('resolution', '0x0').split('x')[1]),
                'fps': int(stream.get('fps'))
            }

        elif stream.get('acodec') != 'none' and stream.get('vcodec') == 'none':
            audio_streams[stream['format_id']] = {
                'ext': stream.get('ext'),
                'filesize': stream.get('filesize', 0),
                'abr': round(stream.get('abr'))
            }

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


def download_and_stream_video(video_url, video_stream_id=None, audio_stream_id=None):
    if video_stream_id and audio_stream_id:
        format_string = f'{video_stream_id}+{audio_stream_id}'
    elif video_stream_id is not None:
        format_string = f'{video_stream_id}/bestaudio'
    else:
        format_string = audio_stream_id

    command = [
        'yt-dlp',
        '-q',
        '--no-warnings',
        '-f', format_string,
        video_url,
        '-o', '-'
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while chunk := process.stdout.read(1024 * 128):
        yield chunk

    _, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Error during yt-dlp execution: {stderr.decode('utf-8')}")
