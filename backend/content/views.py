from django.http import Http404
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.auth import OptionalJWT

from . import serializers as s
from .models import (
    Album, Article, Comment, Devotional, HeroSlide, Lesson, Like, PastorProfile, Sermon,
)

KINDS = {'sermon': Sermon, 'lesson': Lesson, 'devotional': Devotional}


class PublicMixin:
    """Open to visitors. A bad/expired token is ignored rather than rejected."""

    permission_classes = [AllowAny]
    authentication_classes = [OptionalJWT]


class HeroList(PublicMixin, ListAPIView):
    serializer_class = s.HeroSerializer
    queryset = HeroSlide.objects.filter(published=True)


class SermonList(PublicMixin, ListAPIView):
    serializer_class = s.SermonSerializer
    queryset = Sermon.objects.filter(published=True)


class LessonList(PublicMixin, ListAPIView):
    serializer_class = s.LessonSerializer
    queryset = Lesson.objects.filter(published=True)


class DevotionalList(PublicMixin, ListAPIView):
    serializer_class = s.DevotionalSerializer
    queryset = Devotional.objects.filter(published=True)


class GalleryList(PublicMixin, ListAPIView):
    serializer_class = s.AlbumSerializer
    queryset = Album.objects.filter(published=True)


class AboutView(PublicMixin, APIView):
    def get(self, request):
        p = PastorProfile.objects.first()
        return Response(s.PastorSerializer(p).data if p else {})


def article_list(section):
    class _List(PublicMixin, ListAPIView):
        serializer_class = s.ArticleSerializer

        def get_queryset(self):
            return Article.objects.filter(section=section, published=True)

    return _List.as_view()


class FormCreate(CreateAPIView):
    """Open to everyone, but rate-limited per IP and guarded by a hidden honeypot field."""

    permission_classes = [AllowAny]
    authentication_classes = [OptionalJWT]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'forms'

    def create(self, request, *args, **kwargs):
        if request.data.get('website'):  # real people never see this field; bots fill it
            return Response({'ok': True}, status=201)
        return super().create(request, *args, **kwargs)


class PrayerCreate(FormCreate):
    serializer_class = s.PrayerSerializer


class ContactCreate(FormCreate):
    serializer_class = s.ContactSerializer


# ---------- likes & comments ----------
def _target(kind, pk):
    model = KINDS.get(kind)
    if not model or not model.objects.filter(pk=pk, published=True).exists():
        raise Http404
    return model


def _snapshot(request, kind, pk):
    comments = Comment.objects.filter(kind=kind, object_id=pk, approved=True).select_related('user')
    return {
        'likes': Like.objects.filter(kind=kind, object_id=pk).count(),
        'liked': Like.objects.filter(kind=kind, object_id=pk, user=request.user).exists(),
        'comments': s.CommentSerializer(comments, many=True).data,
    }


class EngageView(APIView):
    """GET → current likes/comments for an item."""

    def get(self, request, kind, pk):
        _target(kind, pk)
        return Response(_snapshot(request, kind, pk))


class LikeToggleView(APIView):
    def post(self, request, kind, pk):
        _target(kind, pk)
        like, created = Like.objects.get_or_create(user=request.user, kind=kind, object_id=pk)
        if not created:
            like.delete()
        return Response(_snapshot(request, kind, pk))


class CommentCreateView(APIView):
    def post(self, request, kind, pk):
        _target(kind, pk)
        text = (request.data.get('text') or '').strip()
        if not text:
            return Response({'detail': 'Comment cannot be empty.'}, status=400)
        Comment.objects.create(user=request.user, kind=kind, object_id=pk, text=text[:1000])
        return Response(_snapshot(request, kind, pk), status=201)
