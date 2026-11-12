"""Staff-only JSON API behind the React admin panel (/api/manage/...).

Everything here requires a staff account. It is separate from the public API, so changing it cannot
affect what visitors see. Lists are paginated (20 per page), searchable with ?q= and use lighter
serializers (no long text bodies); the edit form loads the full record.
"""
import time
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from accounts.models import User
from content.models import (
    Album, Article, Comment, ContactMessage, Devotional, HeroSlide, Lesson, PastorProfile,
    PrayerRequest, Sermon,
)
from shop import services
from shop.models import Donation, Order, Payment, Product

from . import serializers as s
from .permissions import IsStaff

# Import Cloudinary only when needed to avoid import errors if CLOUDINARY_URL is not set
try:
    import cloudinary
    from cloudinary.utils import api_sign_request
    CLOUDINARY_AVAILABLE = True
except Exception:
    CLOUDINARY_AVAILABLE = False


class Pager(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class QSearch(SearchFilter):
    search_param = 'q'


class Panel:
    permission_classes = [IsStaff]
    pagination_class = Pager
    filter_backends = [QSearch]


class PanelViewSet(Panel, ModelViewSet):
    list_serializer_class = None

    def get_serializer_class(self):
        if self.action == 'list' and self.list_serializer_class:
            return self.list_serializer_class
        return self.serializer_class


def crud(model, full, light, search, order=None):
    return type(
        f'{model.__name__}Panel', (PanelViewSet,),
        {'queryset': model.objects.all(), 'serializer_class': full, 'list_serializer_class': light,
         'search_fields': search, **({'ordering': order} if order else {})},
    )


HeroView = crud(HeroSlide, s.Hero, s.HeroList, ['title'])
SermonView = crud(Sermon, s.Sermon_, s.SermonList, ['title', 'speaker', 'category'])
LessonView = crud(Lesson, s.Lesson_, s.LessonList, ['title', 'quarter', 'teacher'])
DevotionalView = crud(Devotional, s.Devotional_, s.DevotionalList, ['title', 'author', 'scripture'])
AlbumView = crud(Album, s.Album_, s.AlbumList, ['title', 'location'])
ProductView = crud(Product, s.Product_, s.ProductList, ['name'])


class ArticleView(PanelViewSet):
    serializer_class = s.Article_
    list_serializer_class = s.ArticleList
    search_fields = ['title', 'author', 'category']

    def get_queryset(self):
        qs = Article.objects.all()
        section = self.request.query_params.get('section')
        return qs.filter(section=section) if section else qs


# ---------- inbox: prayers, messages, comments ----------
class PrayerView(Panel, ModelViewSet):
    queryset = PrayerRequest.objects.all()
    serializer_class = s.PrayerSerializer
    search_fields = ['name', 'email', 'request']
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']


class MessageView(Panel, ModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = s.MessageSerializer
    search_fields = ['name', 'email', 'message']
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']


class CommentView(Panel, ModelViewSet):
    queryset = Comment.objects.select_related('user')
    serializer_class = s.CommentSerializer
    search_fields = ['text', 'user__first_name', 'user__email']
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        qs = super().get_queryset()
        kind = self.request.query_params.get('kind')
        return qs.filter(kind=kind) if kind else qs

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        self._titles = _titles(page or [])
        return page

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['titles'] = getattr(self, '_titles', {})
        return ctx


def _titles(comments):
    """{(kind, id): title} for the items these comments belong to (3 queries at most)."""
    wanted = {}
    for c in comments:
        wanted.setdefault(c.kind, set()).add(c.object_id)
    out = {}
    for kind, model in (('sermon', Sermon), ('lesson', Lesson), ('devotional', Devotional)):
        if kind in wanted:
            for pk, title in model.objects.filter(pk__in=wanted[kind]).values_list('pk', 'title'):
                out[(kind, pk)] = title
    return out


# ---------- money ----------
class PaymentView(Panel, ReadOnlyModelViewSet):
    def get_queryset(self):
        qs = super().get_queryset()
        st = self.request.query_params.get('status')
        return qs.filter(status=st) if st in dict(Payment.STATUS) else qs

    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        """For when Safaricom's callback never arrived but the money is in. Sends the receipt email."""
        obj = self.get_object()
        services.mark_paid(obj, (request.data.get('receipt') or '').strip()[:40])
        obj.refresh_from_db()
        return Response(self.get_serializer(obj).data)


class OrderView(PaymentView):
    queryset = Order.objects.select_related('user').prefetch_related('items')
    serializer_class = s.OrderSerializer
    search_fields = ['ref', 'name', 'email', 'phone', 'mpesa_receipt']


class DonationView(PaymentView):
    queryset = Donation.objects.all()
    serializer_class = s.DonationSerializer
    search_fields = ['name', 'email', 'phone', 'mpesa_receipt']


class MemberView(Panel, ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = s.MemberSerializer
    search_fields = ['first_name', 'email']
    http_method_names = ['get', 'patch', 'head', 'options']  # can switch a member on/off, never delete


# ---------- single records ----------
class PastorView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        p = PastorProfile.objects.first()
        return Response(s.Pastor(p).data if p else {})

    def put(self, request):
        p = PastorProfile.objects.first()
        ser = s.Pastor(p, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)

    patch = put


class Stats(APIView):
    """Everything the dashboard needs in a handful of queries."""

    permission_classes = [IsStaff]

    def get(self, request):
        now = timezone.now()
        since = now - timedelta(days=13)
        paid = Q(status=Payment.PAID)
        orders = Order.objects.aggregate(
            total=Count('id'), paid=Count('id', filter=paid), pending=Count('id', filter=Q(status=Payment.PENDING)),
            revenue=Sum('amount', filter=paid),
        )
        gifts = Donation.objects.aggregate(paid=Count('id', filter=paid), total=Sum('amount', filter=paid))

        def per_day(model):
            rows = (model.objects.filter(status=Payment.PAID, created__gte=since)
                    .annotate(d=TruncDate('created')).values('d').annotate(v=Sum('amount')))
            return {r['d']: r['v'] for r in rows}

        o, d = per_day(Order), per_day(Donation)
        today = timezone.localdate()
        days = [today - timedelta(days=i) for i in range(13, -1, -1)]
        series = [{'date': x.isoformat(), 'orders': o.get(x, 0), 'donations': d.get(x, 0)} for x in days]

        return Response({
            'content': {
                'sermons': Sermon.objects.count(), 'lessons': Lesson.objects.count(),
                'devotionals': Devotional.objects.count(), 'articles': Article.objects.count(),
                'albums': Album.objects.count(), 'products': Product.objects.count(),
                'hero': HeroSlide.objects.count(),
            },
            'members': User.objects.count(),
            'inbox': {
                'prayers': PrayerRequest.objects.filter(prayed_for=False).count(),
                'messages': ContactMessage.objects.filter(handled=False).count(),
                'comments': Comment.objects.count(),
            },
            'orders': {'count': orders['total'], 'paid': orders['paid'], 'pending': orders['pending'],
                       'revenue': orders['revenue'] or 0},
            'donations': {'count': gifts['paid'], 'total': gifts['total'] or 0},
            'series': series,
            'recent': {
                'orders': s.OrderSerializer(Order.objects.select_related('user').prefetch_related('items')[:5], many=True).data,
                'prayers': s.PrayerSerializer(PrayerRequest.objects.all()[:5], many=True).data,
                'messages': s.MessageSerializer(ContactMessage.objects.all()[:5], many=True).data,
            },
        })


# ---------- direct-to-Cloudinary uploads ----------
FOLDERS = {'covers', 'posters', 'pdfs', 'pastor', 'products', 'albums', 'videos'}
TYPES = {'image', 'video', 'raw'}


class UploadSign(APIView):
    """Returns a short-lived signature so the browser can upload a file straight to Cloudinary.

    The file never passes through this server (Vercel caps request bodies at ~4.5 MB, and it is faster)."""

    permission_classes = [IsStaff]

    def post(self, request):
        if not CLOUDINARY_AVAILABLE:
            return Response({'detail': 'Cloudinary is not set up on the server (CLOUDINARY_URL).'}, status=503)
        cfg = cloudinary.config()
        if not (cfg.cloud_name and cfg.api_key and cfg.api_secret):
            return Response({'detail': 'Cloudinary is not set up on the server (CLOUDINARY_URL).'}, status=503)
        folder = request.data.get('folder') or 'covers'
        rtype = request.data.get('type') or 'image'
        if folder not in FOLDERS or rtype not in TYPES:
            return Response({'detail': 'Unknown upload type.'}, status=status.HTTP_400_BAD_REQUEST)
        params = {'folder': f'rk/{folder}', 'timestamp': int(time.time())}
        return Response({
            'cloud_name': cfg.cloud_name,
            'api_key': cfg.api_key,
            'timestamp': params['timestamp'],
            'folder': params['folder'],
            'signature': api_sign_request(params, cfg.api_secret),
            'upload_url': f'https://api.cloudinary.com/v1_1/{cfg.cloud_name}/{rtype}/upload',
        })
