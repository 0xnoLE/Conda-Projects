from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Video
import yt_dlp as youtube_dl
import os
from django.conf import settings
import ffmpeg
from yt_dlp.utils import DownloadError, PostProcessingError

def home(request):
    return render(request, 'downloader/home.html')

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
                duration=info['duration']
            )
            video.save()

            audio_dir = os.path.join(settings.MEDIA_ROOT, 'audios')
            os.makedirs(audio_dir, exist_ok=True)
            audio_path = os.path.join(audio_dir, f"{info['title']}.m4a")
            os.rename(video_path.rsplit('.',1)[0] + '.m4a', audio_path)

            return redirect('video_detail', video_id=video.id)

        except DownloadError as e:
            error_message = str(e)
            print(f"Download error: {error_message}")

        except PostProcessingError as e:
            error_message = str(e)
            print(f"Postprocessing error: {error_message}")

        except Exception as e:
            error_message = str(e)
            return HttpResponse(f"Error: {error_message}")

    return render(request, 'downloader/download.html')

def video_detail(request, video_id):
    video = Video.objects.get(id=video_id)
    return render(request, 'downloader/video_detail.html', {'video': video})