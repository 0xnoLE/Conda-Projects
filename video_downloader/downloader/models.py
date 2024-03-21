from django.db import models

class Video(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=255)
    format = models.CharField(max_length=10)
    status = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    published_at = models.DateTimeField(blank=True, null=True)
    duration = models.PositiveIntegerField(default=0)
    video_file = models.FileField(upload_to='videos/', blank=True)
    audio_file = models.FileField(upload_to='audios/', blank=True)
    thumbnail = models.ImageField(upload_to='thumnbails/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.title

# Create your models here.
