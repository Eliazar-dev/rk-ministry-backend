"""Serializers for the React admin panel.

Images/PDFs are uploaded straight from the browser to Cloudinary (see UploadSign), so the panel only
ever saves plain URLs. The old CloudinaryField columns are hidden; whenever a `*_url` value is saved the
matching upload field is cleared so the URL is the single source of truth.
"""
from rest_framework import serializers

from accounts.models import User
from content.models import (
    Album, Article, Comment, ContactMessage, Devotional, HeroSlide, Lesson, PastorProfile,
    PrayerRequest, Sermon,
)
from shop.models import Donation, Order, OrderItem, Product

# upload field -> url field
PAIRS = {'cover': 'cover_url', 'pdf': 'pdf_url', 'poster': 'poster_url', 'photo': 'photo_url', 'image': 'image_url'}
HIDDEN = tuple(PAIRS)


class PanelSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        for cloud in PAIRS:
            if hasattr(instance, f'{cloud}_src'):
                data[f'{cloud}_src'] = getattr(instance, f'{cloud}_src') or ''
        return data

    def _apply(self, validated):
        for cloud, url in PAIRS.items():
            if url in validated and hasattr(self.Meta.model, cloud):
                validated[cloud] = None
        return validated

    def create(self, validated_data):
        return super().create(self._apply(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._apply(validated_data))


def make(model, light=()):
    """Build (full, list) serializers for a model. `light` fields are left out of list responses."""
    hidden = tuple(f for f in HIDDEN if hasattr(model, f))

    def build(name, exclude):
        meta = type('Meta', (), {'model': model, 'exclude': exclude})
        return type(name, (PanelSerializer,), {'Meta': meta})

    return build(f'{model.__name__}Panel', hidden), build(f'{model.__name__}PanelList', hidden + tuple(light))


Hero, HeroList = make(HeroSlide)
Sermon_, SermonList = make(Sermon, light=('description',))
Lesson_, LessonList = make(Lesson, light=('description',))
Devotional_, DevotionalList = make(Devotional, light=('body',))
Article_, ArticleList = make(Article, light=('body',))
Album_, AlbumList = make(Album)
Product_, ProductList = make(Product, light=('description',))
Pastor = make(PastorProfile)[0]


class CommentSerializer(serializers.ModelSerializer):
    member = serializers.CharField(source='user.display_name', read_only=True)
    member_email = serializers.CharField(source='user.email', read_only=True)
    target = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ('id', 'member', 'member_email', 'kind', 'object_id', 'target', 'text', 'approved', 'created')
        read_only_fields = ('kind', 'object_id', 'text', 'created')

    def get_target(self, obj):
        titles = self.context.get('titles') or {}
        key = (obj.kind, obj.object_id)
        if key not in titles:  # single-record update: look it up directly
            from .views import _titles
            titles = _titles([obj])
        return titles.get(key, '')


class PrayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerRequest
        fields = ('id', 'name', 'email', 'request', 'prayed_for', 'created')
        read_only_fields = ('name', 'email', 'request', 'created')


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ('id', 'name', 'email', 'message', 'handled', 'created')
        read_only_fields = ('name', 'email', 'message', 'created')


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('name', 'price', 'qty')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    member_email = serializers.CharField(source='user.email', read_only=True, default='')

    class Meta:
        model = Order
        fields = ('id', 'ref', 'name', 'email', 'phone', 'location', 'amount', 'status', 'mpesa_receipt',
                  'failure_reason', 'created', 'member_email', 'items')


class DonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Donation
        fields = ('id', 'name', 'email', 'phone', 'amount', 'status', 'mpesa_receipt', 'failure_reason', 'created')


class MemberSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='display_name', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'is_staff', 'is_active', 'date_joined', 'last_login')
        read_only_fields = ('name', 'email', 'date_joined', 'last_login')
