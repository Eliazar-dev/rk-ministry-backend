from django.db import migrations

VIDEOS = [
    ('Hope to the Hopeless',
     'https://res.cloudinary.com/dtoxfbfr/video/upload/v1794340688/YTSave.to_YouTube_Media_OwtCx7vlQpQ_HOPE-TO-THE-HOPELESS-Pr-Kwanya-Richard-Snr-HPM-MEDIA-OFFICIAL-VIDEO-4K-VIDEO_003_360p_online-video-cutter.com.mp4'),
    ('The Book of John',
     'https://res.cloudinary.com/dtoxfbfr/video/upload/v1794337983/YTSave.to_YouTube_Media_LWpGMD1tmkk_THE-BOOK-OF-JOHN-Pr-Kwanya-Richard-Snr-HPM-MEDIA-4K-OFFICIAL-VIDEO_001_1080p_online-video-cutter.com.mp4'),
]


def add_videos(apps, schema_editor):
    HeroSlide = apps.get_model('content', 'HeroSlide')
    if HeroSlide.objects.exists():
        return  # never overwrite slides you already added
    for i, (title, url) in enumerate(VIDEOS, start=1):
        HeroSlide.objects.create(title=title, video_url=url, order=i)


class Migration(migrations.Migration):
    dependencies = [('content', '0002_album_pastorprofile_alter_heroslide_poster_url_and_more')]
    operations = [migrations.RunPython(add_videos, migrations.RunPython.noop)]
