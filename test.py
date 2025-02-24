import os, re
import torch
from pathlib import Path
from pytube import YouTube
import whisper
from whisper.utils import get_writer
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# @title Step 1: Enter URL & Choose Whisper Model

# @markdown Enter the URL of the YouTube video
YouTube_URL = "https://www.youtube.com/watch?v=1wFFlTnYWi4"  # @param {type:"string"}

# @markdown Choose the whisper model you want to use
whisper_model = "medium"  # @param ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]

# @markdown Save the transcription as text (.txt) file?
text = True  # @param {type:"boolean"}

# @markdown Save the transcription as an SRT (.srt) file?
srt = True  # @param {type:"boolean"}

# Step 3: Transcribe the video/audio data

device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model(whisper_model).to(device)


# Util function to change name
def to_snake_case(name):
    return name.lower().replace(" ", "_").replace(":", "_").replace("__", "_")


# Download the audio data from YouTube video
def download_audio_from_youtube(url, file_name=None, out_dir="."):
    print(f"\n==> Downloading audio...")
    yt = YouTube(url)
    if file_name is None:
        file_name = Path(out_dir, to_snake_case(yt.title)).with_suffix(".mp4")
    yt = (yt.streams
          .filter(only_audio=True, file_extension="mp4")
          .order_by("abr")
          .desc())
    return yt.first().download(filename=file_name)


# Transcribe the audio data with Whisper
def transcribe_audio(model, file, text, srt):
    print("\n=======================")
    print(f"\n🔗 YouTube URL: {YouTube_URL}")
    print(f"\n🤖 Whisper Model: {whisper_model}")
    print("\n=======================")

    file_path = Path(file)
    output_directory = file_path.parent

    # Run Whisper to transcribe audio
    print(f"\n==> Transcribing audio")
    result = model.transcribe(file, verbose=False)

    if text:
        print(f"\n==> Creating .txt file")
        txt_path = file_path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as txt:
            txt.write(result["text"])
    if srt:
        print(f"\n==> Creating .srt file")
        srt_writer = get_writer("srt", output_directory)
        srt_writer(result, str(file_path.stem))

    # Download the transcribed files locally
    from google.colab import files

    colab_files = Path("/content")
    stem = file_path.stem

    for colab_file in colab_files.glob(f"{stem}*"):
        if colab_file.suffix in [".txt", ".srt"]:
            files.download(str(colab_file))

    print("\n✨ All Done!")
    print("=======================")
    return result


# Download & Transcribe the audio data
audio = download_audio_from_youtube(YouTube_URL)
result = transcribe_audio(model, audio, text, srt)
