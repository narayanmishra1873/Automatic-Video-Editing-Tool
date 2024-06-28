import time
import math
import ffmpeg
from moviepy.editor import VideoFileClip, concatenate_videoclips
from faster_whisper import WhisperModel
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
import os
import subprocess



# Get the frame rate from the pre-video (assuming all videos have the same frame rate)
input_video = input("Enter the video path  (include format)   :  ")
output_video = input("Enter output path    (include format)    :  ")
width, height = 1280, 720

video = VideoFileClip(input_video)
# Get the video size (width and height)
width1, height1 = video.size
if(width1<=height):
    width , height = 720, 1280
else:
    width , height = 1280, 720

def resize_video(input_path, output_path, width, height):
    command = [
        'ffmpeg',
        '-i', input_path,
        '-vf', f'scale={width}:{height}',
        output_path
    ]
    subprocess.run(command, check=True)

def extract_audio():
    extracted_audio = f"audio.wav"
    stream = ffmpeg.input(input_video)
    stream = ffmpeg.output(stream, extracted_audio)
    ffmpeg.run(stream, overwrite_output=True)
    return extracted_audio

def transcribe(audio):
    model = WhisperModel("small")
    segments, info = model.transcribe(audio)
    language = info[0]
    print("Transcription language", info[0])
    segments = list(segments)
    for segment in segments:
        # print(segment)
        print("[%.2fs -> %.2fs] %s" %
              (segment.start, segment.end, segment.text))
    return language, segments

def format_time(seconds):

    hours = math.floor(seconds / 3600)
    seconds %= 3600
    minutes = math.floor(seconds / 60)
    seconds %= 60
    milliseconds = round((seconds - math.floor(seconds)) * 1000)
    seconds = math.floor(seconds)
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:01d},{milliseconds:03d}"

    return formatted_time

def generate_subtitle_file(language, segments):

    subtitle_file = f"sub.srt"
    text = ""
    for index, segment in enumerate(segments):
        segment_start = format_time(segment.start)
        segment_end = format_time(segment.end)
        text += f"{str(index+1)} \n"
        text += f"{segment_start} --> {segment_end} \n"
        text += f"{segment.text} \n"
        text += "\n"
        
    f = open(subtitle_file, "w")
    f.write(text)
    f.close()

    return subtitle_file

def add_subtitle_to_video(soft_subtitle, subtitle_file,  subtitle_language):

    video_input_stream = ffmpeg.input(input_video)
    subtitle_input_stream = ffmpeg.input(subtitle_file)
    output_video = f"output.mp4"
    subtitle_track_title = subtitle_file.replace(".srt", "")

    if soft_subtitle:
        stream = ffmpeg.output(
            video_input_stream, subtitle_input_stream, output_video, **{"c": "copy", "c:s": "mov_text"},
            **{"metadata:s:s:0": f"language={subtitle_language}",
            "metadata:s:s:0": f"title={subtitle_track_title}"}
        )
        ffmpeg.run(stream, overwrite_output=True)
    else:
        stream = ffmpeg.output(video_input_stream, output_video,

                               vf=f"subtitles={subtitle_file}")

        ffmpeg.run(stream, overwrite_output=True)


def run():
    extracted_audio = extract_audio()
    language, segments = transcribe(audio=extracted_audio)
    subtitle_file = generate_subtitle_file(
        language=language,
        segments=segments
    )

    add_subtitle_to_video(
        soft_subtitle=False,
        subtitle_file=subtitle_file,
        subtitle_language=language
    )


resize_video(input_video,"resize.mp4",width,height)
input_video = "resize.mp4"
run()
os.remove("audio.wav")
os.remove("sub.srt")
pre_video = VideoFileClip("Assets/PreVideo.mp4")
main_video = VideoFileClip("output.mp4")
post_video = VideoFileClip("Assets/PostVideo.mp4")

# Get the frame rate from the pre-video (assuming all videos have the same frame rate)
target_fps = pre_video.fps
main_video = main_video.set_fps(target_fps)

# Concatenate the videos
final_video = concatenate_videoclips([pre_video, main_video, post_video],method="compose")

background_music = AudioFileClip("Assets/Impactis backgroundmusic.mp3")
background_music = background_music.subclip(0, final_video.duration)
final_audio = CompositeAudioClip([final_video.audio, background_music])
final_video = final_video.set_audio(final_audio)

# Save the final video to a file
final_video.write_videofile(output_video, codec="libx264", audio_codec="aac")
os.remove("output.mp4")
os.remove("resize.mp4")
