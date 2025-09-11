from flask import Flask, render_template, request, Response, stream_with_context
import youtube_utils as yt

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
def download():
    url = request.args.get('url')
    video_stream_id = request.args.get('video-stream-id')
    audio_stream_id = request.args.get('audio-stream-id')

    print(url)
    print(video_stream_id)
    print(audio_stream_id)

    streamer = yt.download_and_stream_video(url, video_stream_id, audio_stream_id)
    return Response(stream_with_context(streamer))


if __name__ == '__main__':
    app.run(debug=True)