"""Field names match what the React frontend expects.

Public pages are open to visitors, but the actual content (video links, PDFs, article text, album links)
is removed on the server for anyone who is not signed in, and the item is flagged "locked": true.
"""
from rest_framework import serializers

from .models import (
    Album, Article, Comment, ContactMessage, Devotional, HeroSlide, Lesson, Like,
    PastorProfile, PrayerRequest, Sermon,
)


def like_count(kind, pk):
    return Like.objects.filter(kind=kind, object_id=pk).count()


class Gated(serializers.ModelSerializer):
    """Drops `locked_fields` for visitors and adds a `locked` flag."""

    locked_fields = ()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        authed = bool(request and request.user and request.user.is_authenticated)
        if not authed:
            for f in self.locked_fields:
                data.pop(f, None)
        data['locked'] = not authed
        return data


class HeroSerializer(serializers.ModelSerializer):
    video = serializers.CharField(source='video_url')
    poster = serializers.CharField(source='poster_auto')

    class Meta:
        model = HeroSlide
        fields = ('id', 'video', 'poster')


class SermonSerializer(Gated):
    locked_fields = ('youtube',)
    cover = serializers.CharField(source='cover_src')
    youtube = serializers.CharField(source='youtube_url')
    likes = serializers.SerializerMethodField()

    class Meta:
        model = Sermon
        fields = ('id', 'title', 'speaker', 'date', 'category', 'cover', 'youtube', 'likes', 'description')

    def get_likes(self, obj):
        return like_count('sermon', obj.pk)


class LessonSerializer(Gated):
    locked_fields = ('youtube', 'pdf')
    cover = serializers.CharField(source='cover_src')
    pdf = serializers.CharField(source='pdf_src')
    hasPdf = serializers.SerializerMethodField()
    youtube = serializers.CharField(source='youtube_url')
    dateRange = serializers.CharField(source='date_range')
    category = serializers.CharField(source='quarter')
    likes = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ('id', 'title', 'quarter', 'dateRange', 'category', 'teacher', 'cover', 'pdf', 'hasPdf',
                  'youtube', 'likes', 'description')

    def get_likes(self, obj):
        return like_count('lesson', obj.pk)

    def get_hasPdf(self, obj):
        return bool(obj.pdf_src)


class DevotionalSerializer(Gated):
    locked_fields = ('body',)
    cover = serializers.CharField(source='cover_src')
    likes = serializers.SerializerMethodField()

    class Meta:
        model = Devotional
        fields = ('id', 'title', 'author', 'date', 'scripture', 'category', 'excerpt', 'body', 'cover', 'likes')

    def get_likes(self, obj):
        return like_count('devotional', obj.pk)


class ArticleSerializer(Gated):
    locked_fields = ('body', 'pdf')
    cover = serializers.CharField(source='cover_src')
    pdf = serializers.CharField(source='pdf_src')
    hasPdf = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ('id', 'title', 'author', 'date', 'category', 'excerpt', 'body', 'cover', 'pdf', 'hasPdf')

    def get_hasPdf(self, obj):
        return bool(obj.pdf_src)


class AlbumSerializer(Gated):
    locked_fields = ('link',)
    cover = serializers.CharField(source='cover_src')
    link = serializers.CharField(source='photos_url')
    year = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = ('id', 'title', 'date', 'year', 'description', 'location', 'cover', 'link')

    def get_year(self, obj):
        return obj.date.year


class PastorSerializer(serializers.ModelSerializer):
    photo = serializers.CharField(source='photo_src')
    intro = serializers.CharField(source='short_intro')

    class Meta:
        model = PastorProfile
        fields = ('name', 'title', 'photo', 'intro', 'biography', 'quote')


class PrayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerRequest
        fields = ('name', 'email', 'request')


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'message')


class CommentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.display_name')
    at = serializers.DateTimeField(source='created')

    class Meta:
        model = Comment
        fields = ('id', 'name', 'text', 'at')
