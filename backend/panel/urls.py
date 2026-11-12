from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views as v

router = SimpleRouter()
router.register('hero', v.HeroView, basename='panel-hero')
router.register('sermons', v.SermonView, basename='panel-sermons')
router.register('lessons', v.LessonView, basename='panel-lessons')
router.register('devotionals', v.DevotionalView, basename='panel-devotionals')
router.register('articles', v.ArticleView, basename='panel-articles')
router.register('albums', v.AlbumView, basename='panel-albums')
router.register('products', v.ProductView, basename='panel-products')
router.register('comments', v.CommentView, basename='panel-comments')
router.register('prayers', v.PrayerView, basename='panel-prayers')
router.register('messages', v.MessageView, basename='panel-messages')
router.register('orders', v.OrderView, basename='panel-orders')
router.register('donations', v.DonationView, basename='panel-donations')
router.register('members', v.MemberView, basename='panel-members')

urlpatterns = [
    path('stats/', v.Stats.as_view()),
    path('pastor/', v.PastorView.as_view()),
    path('upload-sign/', v.UploadSign.as_view()),
    path('', include(router.urls)),
]
