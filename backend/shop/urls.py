from django.urls import path

from . import views

urlpatterns = [
    path('products/', views.ProductList.as_view()),
    path('orders/', views.OrderCreate.as_view()),
    path('orders/<int:pk>/', views.OrderDetail.as_view()),
    path('donations/', views.DonationCreate.as_view()),
    path('donations/<int:pk>/', views.DonationDetail.as_view()),
    path('mpesa/callback/', views.MpesaCallback.as_view()),
]
