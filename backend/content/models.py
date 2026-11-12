from cloudinary.models import CloudinaryField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def media_url(f):
    try:
        return f.url if f else ''
    except Exception:
        return ''


class Base(models.Model):
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Cover(Base):
    """Cover image: upload to Cloudinary from the admin, or paste an existing Cloudinary/any image URL."""

    cover = CloudinaryField('cover image (upload)', folder='rk/covers', blank=True, null=True)
    cover_url = models.URLField('cover image URL', blank=True, help_text='Optional: paste a Cloudinary image URL instead of uploading.')

    class Meta:
        abstract = True

    @property
    def cover_src(self):
        return media_url(self.cover) or self.cover_url


def video_poster(url):
    """First frame of a Cloudinary video as a small JPEG (used as the poster while the video loads)."""
    marker = '/video/upload/'
    if marker not in url or not url.lower().endswith(('.mp4', '.mov', '.webm')):
        return ''
    head, tail = url.split(marker, 1)
    tail = tail.rsplit('.', 1)[0] + '.jpg'
    return f'{head}{marker}so_1,c_limit,w_1280,q_auto/{tail}'


# ---------------- Home page video carousel ----------------
class HeroSlide(Base):
    title = models.CharField(max_length=120, blank=True, help_text='Internal label only.')
    video_url = models.URLField('Cloudinary video URL', max_length=600, help_text='Paste the Cloudinary video link (mp4).')
    poster = CloudinaryField('poster image (optional)', folder='rk/posters', blank=True, null=True)
    poster_url = models.URLField('poster image URL (optional)', max_length=600, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'carousel video'

    @property
    def poster_src(self):
        return media_url(self.poster) or self.poster_url

    @property
    def poster_auto(self):
        return self.poster_src or video_poster(self.video_url)

    def __str__(self):
        return self.title or f'Slide {self.pk}'


# ---------------- Sermons ----------------
class Sermon(Cover):
    title = models.CharField(max_length=200)
    speaker = models.CharField(max_length=120, default='Richard Kwanya Snr')
    date = models.DateField(default=timezone.localdate)
    category = models.CharField(max_length=60, blank=True)
    youtube_url = models.URLField('YouTube link', help_text='Paste the YouTube watch/share link. The site embeds it automatically.')
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.title


# ---------------- Sabbath school ----------------
class Lesson(Cover):
    title = models.CharField(max_length=200)
    quarter = models.CharField(max_length=40, help_text='e.g. Q4 2026')
    date_range = models.CharField(max_length=60, help_text='e.g. Nov 1 – Nov 7')
    teacher = models.CharField(max_length=120, default='Richard Kwanya Snr')
    pdf = CloudinaryField('lesson PDF (upload)', resource_type='raw', folder='rk/pdfs', blank=True, null=True)
    pdf_url = models.URLField('lesson PDF URL', blank=True, help_text='Optional: paste a PDF link (use this for files over 4 MB).')
    youtube_url = models.URLField('YouTube lesson video link')
    description = models.TextField(blank=True)
    start_date = models.DateField(default=timezone.localdate, help_text='Used for ordering — newest first.')

    class Meta:
        ordering = ['-start_date', '-id']

    @property
    def pdf_src(self):
        return media_url(self.pdf) or self.pdf_url

    def __str__(self):
        return f'{self.quarter} — {self.title}'


# ---------------- Devotionals ----------------
class Devotional(Cover):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120, default='Richard Kwanya Snr')
    date = models.DateField(default=timezone.localdate)
    scripture = models.CharField(max_length=80, blank=True, help_text='e.g. Psalm 5:3')
    category = models.CharField(max_length=60, blank=True, default='Daily')
    excerpt = models.CharField(max_length=300, blank=True)
    body = models.TextField()

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return self.title


# ---------------- Blogs, literature, medical, children, ebooks ----------------
class Article(Cover):
    SECTIONS = [
        ('blog', 'Blog'),
        ('literature', 'Literature Evangelism'),
        ('medical', 'Medical Missionary'),
        ('children', 'Children Bible Story'),
        ('ebook', 'E-Book'),
    ]
    section = models.CharField(max_length=20, choices=SECTIONS)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120, default='Richard Kwanya Snr')
    date = models.DateField(default=timezone.localdate)
    category = models.CharField(max_length=60, blank=True)
    excerpt = models.CharField(max_length=300, blank=True)
    body = models.TextField(blank=True)
    pdf = CloudinaryField('PDF (upload, for e-books)', resource_type='raw', folder='rk/pdfs', blank=True, null=True)
    pdf_url = models.URLField('PDF URL', blank=True)

    class Meta:
        ordering = ['-date', '-id']

    @property
    def pdf_src(self):
        return media_url(self.pdf) or self.pdf_url

    def __str__(self):
        return f'[{self.get_section_display()}] {self.title}'


# ---------------- Mission gallery ----------------
class GalleryItem(Cover):
    title = models.CharField(max_length=160)
    category = models.CharField(max_length=60, blank=True)
    date = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'gallery photo'

    def __str__(self):
        return self.title


# ---------------- Mission albums (photos live on an outside site; only the cover is stored here) ----------------
def https_only(value):
    if not str(value).lower().startswith('https://'):
        raise ValidationError('The photo album link must start with https://')


class Album(Cover):
    title = models.CharField('mission name', max_length=160)
    date = models.DateField(default=timezone.localdate)
    location = models.CharField(max_length=120, blank=True)
    description = models.CharField(max_length=300, blank=True)
    photos_url = models.URLField(
        'photo album link', max_length=600, validators=[https_only],
        help_text='Paste the link to the full photo album (Pixieset, Google Photos, etc.). '
                  'Photos are NOT stored on this website, only the cover image.',
    )

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'gallery album'

    @property
    def cover_src(self):
        """Cloudinary covers are served resized and compressed to save bandwidth."""
        if self.cover:
            try:
                return self.cover.build_url(width=800, crop='limit', quality='auto', fetch_format='auto')
            except Exception:
                return media_url(self.cover)
        return self.cover_url

    def __str__(self):
        return f'{self.title} ({self.date:%b %Y})'


# ---------------- Pastor biography (one record) ----------------
class PastorProfile(models.Model):
    name = models.CharField(max_length=120, default='Richard Kwanya Snr')
    title = models.CharField(max_length=120, blank=True, help_text='e.g. Evangelist & Founder')
    photo = CloudinaryField('photo (upload)', folder='rk/pastor', blank=True, null=True)
    photo_url = models.URLField('photo URL', max_length=600, blank=True, help_text='Optional: paste an image URL instead of uploading.')
    short_intro = models.CharField(max_length=300, blank=True)
    biography = models.TextField(blank=True, help_text='Leave a blank line between paragraphs.')
    quote = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name = 'pastor profile'
        verbose_name_plural = 'pastor profile'

    @property
    def photo_src(self):
        if self.photo:
            try:
                return self.photo.build_url(width=900, crop='limit', quality='auto', fetch_format='auto')
            except Exception:
                return media_url(self.photo)
        return self.photo_url

    def __str__(self):
        return self.name


# ---------------- Forms from the site ----------------
class PrayerRequest(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    request = models.TextField()
    prayed_for = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} — {self.created:%d %b %Y}'


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    handled = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.name} — {self.created:%d %b %Y}'


# ---------------- Likes & comments on sermons / lessons / devotionals ----------------
KIND_CHOICES = [('sermon', 'Sermon'), ('lesson', 'Sabbath lesson'), ('devotional', 'Devotional')]


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes')
    kind = models.CharField(max_length=12, choices=KIND_CHOICES)
    object_id = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'kind', 'object_id')


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    kind = models.CharField(max_length=12, choices=KIND_CHOICES)
    object_id = models.PositiveIntegerField()
    text = models.TextField(max_length=1000)
    approved = models.BooleanField(default=True, help_text='Untick to hide this comment from the site.')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.user.display_name}: {self.text[:40]}'
