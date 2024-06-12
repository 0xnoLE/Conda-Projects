from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('download/', views.download_video, name='download_video'),
    path('video/<int:video_id>/', views.video_detail, name='video_detail'),
]