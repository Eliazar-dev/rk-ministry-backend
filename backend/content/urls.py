from django.urls import path

from . import views

urlpatterns = [
    path('hero/', views.HeroList.as_view()),
    path('sermons/', views.SermonList.as_view()),
    path('lessons/', views.LessonList.as_view()),
    path('devotionals/', views.DevotionalList.as_view()),
    path('blogs/', views.article_list('blog')),
    path('literature/', views.article_list('literature')),
    path('medical/', views.article_list('medical')),
    path('children/', views.article_list('children')),
    path('ebooks/', views.article_list('ebook')),
    path('gallery/', views.GalleryList.as_view()),
    path('about/', views.AboutView.as_view()),
    path('prayer-requests/', views.PrayerCreate.as_view()),
    path('contact/', views.ContactCreate.as_view()),
    path('engage/<str:kind>/<int:pk>/', views.EngageView.as_view()),
    path('engage/<str:kind>/<int:pk>/like/', views.LikeToggleView.as_view()),
    path('engage/<str:kind>/<int:pk>/comments/', views.CommentCreateView.as_view()),
]
