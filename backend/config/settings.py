import os
from datetime import timedelta
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key, default=''):
    return os.environ.get(key, default)


def env_list(key, default=''):
    return [v.strip() for v in env(key, default).split(',') if v.strip()]


DEBUG = env('DEBUG', '0') == '1'
SECRET_KEY = env('SECRET_KEY', 'dev-insecure-key-change-me')
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', '.vercel.app,localhost,127.0.0.1,testserver')
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', 'https://*.vercel.app')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'accounts',
    'content',
    'shop',
    'monitoring',
    'panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Vercel's filesystem is read-only/ephemeral: use Postgres (Neon / Supabase / Vercel Postgres) via DATABASE_URL.
if env('DATABASE_URL'):
    DATABASES = {'default': dj_database_url.parse(env('DATABASE_URL'), conn_max_age=60, ssl_require=not DEBUG)}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}

AUTH_USER_MODEL = 'accounts.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Static files (admin CSS) served by WhiteNoise; finders mean no collectstatic step is needed on Vercel.
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# ---- REST + JWT ----
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    # Safe default: anything not explicitly opened to visitors needs an account.
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_PAGINATION_CLASS': None,
    # Only the prayer/contact forms use throttling (scope "forms"); nothing else is throttled.
    'DEFAULT_THROTTLE_RATES': {'forms': env('FORMS_THROTTLE_RATE', '10/hour')},
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}

# ---- CORS ----
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS', 'http://localhost:5173')
CORS_ALLOWED_ORIGIN_REGEXES = env_list('CORS_ALLOWED_ORIGIN_REGEXES', '')

# ---- Email (order receipts, donations) ----
if env('EMAIL_HOST_USER'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(env('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'Richard Kwanya Snr Ministry <no-reply@richardkwanya.org>')

# ---- Cloudinary (reads CLOUDINARY_URL from the environment) ----
# CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>

# ---- M-Pesa Daraja (STK push). Leave blank to run in simulate mode. ----
MPESA_ENV = env('MPESA_ENV', 'sandbox')  # sandbox | production
MPESA_CONSUMER_KEY = env('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = env('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = env('MPESA_SHORTCODE', '174379')
MPESA_PASSKEY = env('MPESA_PASSKEY')
MPESA_CALLBACK_URL = env('MPESA_CALLBACK_URL')  # https://<backend>.vercel.app/api/mpesa/callback/

# ---- Google sign-in (OAuth Web client ID from Google Cloud Console) ----
GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID')

SITE_NAME = 'Richard Kwanya Snr Ministry'
FRONTEND_URL = env('FRONTEND_URL', 'http://localhost:5173').rstrip('/')  # used in password-reset emails
