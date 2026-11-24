from django.urls import path
from .views import NewsletterSubscribe, NewsletterUnsubscribe, NewsletterList, NewsletterMe

urlpatterns = [
    path('subscribe/', NewsletterSubscribe.as_view(), name='newsletter-subscribe'),
    path('unsubscribe/', NewsletterUnsubscribe.as_view(), name='newsletter-unsubscribe'),
    path('subscribers/', NewsletterList.as_view(), name='newsletter-list'),
    path('me/', NewsletterMe.as_view(), name='newsletter-me'),
]
