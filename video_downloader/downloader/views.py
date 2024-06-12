from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Video
import yt_dlp as youtube_dl
import os
from django.conf import settings
import ffmpeg
from yt_dlp.utils import DownloadError, PostProcessingError
import re
from django.shortcuts import get_object_or_404, redirect
import subprocess
import shutil

def home(request):
    return render(request, 'downloader/home.html')

def sanitize_filename(filename):
    """
    Remove any invalid characters from the filename and replace with underscores.
    """
    filename = re.sub(r'(?<=\W)\s+(?=\W)', '_', filename)
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    return filename

    
def download_video(request):
    if request.method == 'POST':
        url = request.POST['url']
        # Extract video information and initiate download
        # Save video details to the database
        ydl_opts = {
            'verbose': True,
            'outtmpl': {
                'default': os.path.join(settings.MEDIA_ROOT, 'videos', '%(title)s.%(ext)s'),
                'aac': os.path.join(settings.MEDIA_ROOT, 'audios', '%(title)s.%(ext)s'),
            },
            'format': 'bestvideo+bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'aac',
                'preferredquality': '192',
            }],
            'prefer_ffmpeg': True,
        }
        try:
            # Extract video info and download the video
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url)
                video_path = ydl.prepare_filename(info)

            # Save video info to the database
            video = Video(
                url=url,
                title=info['title'],
                description=info['description'],
                thumbnail=info['thumbnail'],
                published_at=info['upload_date'],
                duration=info['duration'],
                video_file = video_path,
            )
            video.save()


            sanitized_title = sanitize_filename(info['title'])

                #Extract audio using FFmpeg
            stream = ffmpeg.input(video_path)
            
            audio_file = f"{sanitized_title}.m4a"
            audio_path = os.path.join(settings.MEDIA_ROOT, 'audios', audio_file)
            
            try:
                audio_stream = ffmpeg.output(stream, audio_path, acodec='libfdk_aac', audio_bitrate='192k')
                ffmpeg.run(audio_stream, overwrite_output=True)
            except ffmpeg.Error as e: 
                error_message = str(e)
                print(f"FFmpeg error: {error_message}")

                video_audio_path = os.path.join(settings.MEDIA_ROOT, 'videos', audio_file)
                if os.path.exists(video_audio_path):
                    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                    shutil.move(video_audio_path, audio_path)
                    print(f"Audio file moved from 'videos' to 'audios' directory: {audio_file}")
                else:
                    return HttpResponse(f"Error: {error_message}")
        
            #Up[date the audio file path in the Video model
            video.audio_file.name = os.path.join('audios', audio_file)
            video.save()

            return redirect('video_detail',video_id=video.id)
    
        except (DownloadError, PostProcessingError) as e:
            error_message = str(e)
            print(f"Error: {error_message}")
            return HttpResponse(f"Error: {error_message}")
            
    return render(request, 'downloader/download.html')

def pitch_shift(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    if request.method == 'POST':
        pitch_shift_value = float(request.POST.get('pitch_shift', 1.0))

        audio_file_path = video.audio_file.path
        if not os.path.exists(audio_file_path):
            error_message = f"Audio file not found: {audio_file_path}"
            print(error_message)
            return HttpResponse(f"Error: {error_message}")
        
        sanitized_title = sanitize_filename(video.title)
        pitch_shifted_audio_file = f"{sanitized_title}_pitch_shifted.m4a"
        pitch_shifted_audio_path = os.path.join(settings.MEDIA_ROOT, 'audios', pitch_shifted_audio_file)

        try:
            input_stream = ffmpeg.input(audio_file_path)
            output_stream = (
                input_stream
                .filter('asetrate',44100 * pitch_shift_value)
                .filter('aresample', 44100)
                .output(pitch_shifted_audio_path, acodec='aac', audio_bitrate='192k')
            )
            ffmpeg.run(output_stream, overwrite_output=True)
        except ffmpeg.Error as e:
            error_message = str(e)
            print(f"FFMpeg error: {error_message}")
            return HttpResponse(f"Error: {error_message}")

        #audio_dir = os.path.join(settings.MEDIA_ROOT, 'audios')
        #os.makedirs(audio_dir, exist_ok=True)
        #sanitized_title = sanitize_filename(video.title)
        #pitch_shifted_audio_path = os.path.join(audio_dir, f"{sanitized_title}_pitch_shifted.m4a")
        #ffmpeg.run(output_stream, pitch_shifted_audio_path, overwrite_output=True)

        video.pitch_shifted_audio_file.name = os.path.join('audios', f"{sanitized_title}_pitch_shifted.m4a")
        video.save()

    return redirect('video_detail', video_id=video.id) 
def video_detail(request, video_id):
    video = Video.objects.get(id=video_id)
    context = {
        'video': video,
        'video_file': video.video_file.url if video.video_file else None,
        'audio_file': video.audio_file.url if video.audio_file else None,
        'pitch_shifted_audio_file': video.pitch_shifted_audio_file.url if video.pitch_shifted_audio_file else None,
    }
    return render(request, 'downloader/video_detail.html', context)
