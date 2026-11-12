from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view()),         # step 1: details -> emails a code
    path('auth/verify/', views.VerifySignupView.as_view()),       # step 2: code -> account + tokens
    path('auth/login/', views.LoginView.as_view()),
    path('auth/otp/request/', views.LoginCodeRequestView.as_view()),
    path('auth/otp/login/', views.LoginCodeVerifyView.as_view()),
    path('auth/google/', views.GoogleLoginView.as_view()),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('auth/forgot/', views.ForgotPasswordView.as_view()),
    path('auth/reset/', views.ResetPasswordView.as_view()),
    path('auth/me/', views.MeView.as_view()),
]
