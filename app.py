from flask import Flask, render_template, request, Response, stream_with_context
import youtube_utils as yt

app = Flask(__name__)
LAST_VIDEO_DATA = None

@app.route('/')
def index():
    global LAST_VIDEO_DATA
    url = request.args.get('url')
    if url is not None:
        video_data = yt.get_video_data(url)
        LAST_VIDEO_DATA = video_data
    else:
        video_data = None
        LAST_VIDEO_DATA = None

    return render_template('index.html', video=video_data)


@app.route('/download/')
def download():
    stream_id = request.args.get('stream-id')
    stream_type = request.args.get('type')

    if LAST_VIDEO_DATA is None:
        return "No video data found. Please search for a video first.", 404

    download_name = LAST_VIDEO_DATA.get('title', 'video')

    if stream_type == 'video':
        video_stream_id = stream_id
        stream_data = LAST_VIDEO_DATA['streams']['video'][int(video_stream_id)]
        video_stream_id = stream_data['id']
        audio_stream_id = stream_data['audio_stream_id']
        ext = stream_data['ext']
    elif stream_type == 'audio':
        video_stream_id = None
        audio_stream_id = stream_id
        stream_data = LAST_VIDEO_DATA['streams']['audio'][int(audio_stream_id)]
        ext = stream_data['ext']
    else:
        return 'Invalid stream type', 403

    headers = {
        "Content-Disposition": f'attachment; filename="{download_name}.{ext}"',
        "Content-Type": f"{stream_type}/{ext}"
    }

    if ext != 'mp4':
        headers['Content-Length'] = stream_data['filesize']

    streamer = yt.download_and_stream_video(LAST_VIDEO_DATA['url'], video_stream_id, audio_stream_id)
    return Response(stream_with_context(streamer), headers=headers)


if __name__ == '__main__':
    app.run(debug=True)