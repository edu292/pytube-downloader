import tkinter as tk
from pytubefix import YouTube
from tkinter import filedialog
import subprocess
import urllib
from io import BytesIO
from PIL import ImageTk, Image
import urllib.request
import os
import textwrap
import threading


def show_thumbnail(title, url):
    with urllib.request.urlopen(url) as u:
        raw_data = u.read()
    im = Image.open(BytesIO(raw_data))
    im = im.resize((320, 240), Image.LANCZOS)
    im = im.crop((0, 30, 320, 210))
    photo = ImageTk.PhotoImage(im)
    images.append(photo)

    thumbnail_label.config(image=photo)
    title_label.config(text=textwrap.fill(title, width=40))

def sort_stream_helper(stream):
    if stream.type == 'audio':
        return int(stream.abr.strip('kbps')) - 160
    else:
        return int(stream.resolution.strip('p'))

def sort_download_option(resolution):
    if 'kbps' in resolution:
        return int(resolution.split('k')[0]) - 160
    else:
        return int(resolution.split('p')[0])


def sort_streams(streams):
    sorted_streams = streams.filter(only_audio=True).all()
    sorted_streams += streams.filter(progressive=True).all()
    download_options = [f'{stream.resolution}/{stream.subtype}' if stream.type == 'video'
                        else f'{stream.abr}/{stream.subtype}' for stream in sorted_streams]
    for stream in streams.filter(only_video=True):
        if stream.subtype == 'mp4':
            if f'{stream.resolution}/mp4' in download_options:
                continue
        sorted_streams.append(stream)
        download_options.append(f'{stream.resolution}/{stream.subtype}')

    sorted_streams.sort(key=sort_stream_helper, reverse=True)
    download_options.sort(key=sort_download_option, reverse=True)

    return download_options, sorted_streams


def populate_download_frame(download_options):
    selected_option.set(download_options[0])
    download_options_menu = tk.OptionMenu(download_frame, selected_option, *download_options)
    download_options_menu.grid(row=0, column=0)
    download_button.grid()

def show_file_size():
    file_size = streams[download_options.index(selected_option.get())].filesize
    file_size_label.config(text=file_size)


def search():
    url = url_entry.get()
    yt = YouTube(url)
    show_thumbnail(yt.title, yt.thumbnail_url)
    global streams, download_options
    streams = yt.streams
    download_options, streams = sort_streams(streams)
    populate_download_frame(download_options)


def get_audio_stream(resolution):
    audio_streams = [stream for stream in streams if stream.type == 'audio']
    audio_streams.reverse()
    download_options.reverse()
    audio_stream_index = (download_options.index(resolution) - len(audio_streams)) // 2
    if audio_stream_index >= len(audio_streams):
        audio_stream_index = len(audio_streams) - 1
    audio_stream = audio_streams[audio_stream_index]

    return audio_stream


def merge_files(download_directory, audio_file_name, video_file_name, output_file_name):
    audio_file_path = os.path.abspath(audio_file_name)
    video_file_path = os.path.abspath(video_file_name)
    output_file_path = os.path.join(download_directory, output_file_name)
    command = f'ffmpeg -i "{video_file_path}" -i "{audio_file_path}" -c:v copy "{output_file_path}"'
    subprocess.run(command, creationflags=subprocess.CREATE_NO_WINDOW)
    os.remove(audio_file_path)
    os.remove(video_file_path)


def download():
    resolution = selected_option.get()
    download_directory = filedialog.askdirectory()
    selected_stream = streams[download_options.index(resolution)]
    if selected_stream.type == 'audio' or selected_stream.is_progressive:
        selected_stream.download(download_directory)
    else:
        audio_stream = get_audio_stream(resolution)
        audio_file_name = f'audiotemp.{audio_stream.subtype}'
        video_file_name = f'videotemp.{selected_stream.subtype}'
        audio_stream.download(os.path.abspath('.'), filename=audio_file_name)
        selected_stream.download(os.path.abspath('.'), filename=video_file_name)
        threading.Thread(
            target=merge_files,
            args=(download_directory, audio_file_name, video_file_name, selected_stream.default_filename),
            daemon=True
        ).start()


window = tk.Tk()
window.geometry('750x350')
window.title('Youtube Downloader')

search_frame = tk.Frame(window, pady=10)
url_entry = tk.Entry(search_frame, width=50)
url_entry.pack(side=tk.LEFT)

search_button = tk.Button(search_frame, text='Search', command=search)
search_button.pack(side=tk.LEFT)

search_frame.pack(anchor=tk.CENTER)

selected_option = tk.StringVar()
images = []
video_frame = tk.Frame(window, pady=40, padx=20)
selected_option.trace_add('write', lambda x, y, z: show_file_size())

thumbnail_label = tk.Label(video_frame)
thumbnail_label.grid(row=0, column=0, rowspan=3, columnspan=2)

title_label = tk.Label(video_frame)
title_label.grid(row=0, column=2, columnspan=2)

download_frame = tk.Frame(video_frame)
download_frame.grid(row=1, column=2, columnspan=2)

streams = []
download_options = []

download_button = tk.Button(download_frame, text='Download', command=download)
download_button.grid(row=0, column=1)
download_button.grid_forget()

file_size_label = tk.Label(download_frame)
file_size_label.grid(row=1, column=1)

video_frame.pack(side=tk.TOP)

window.mainloop()
