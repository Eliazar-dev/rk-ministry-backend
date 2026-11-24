"""Authentication: email OTP sign-up and login, optional passwords, Google sign-in, JWT.

Flow
----
Sign up   : POST /auth/register/ {name, email, password?}  -> emails a 6-digit code
            POST /auth/verify/   {email, code}             -> creates the account, returns JWT
Log in    : POST /auth/login/    {email, password}         -> JWT (only if a password was set)
            POST /auth/otp/request/ {email}                -> emails a login code (always 200)
            POST /auth/otp/login/   {email, code}          -> JWT
Google    : POST /auth/google/    {credential}             -> JWT (creates the account on first use)
Password  : POST /auth/password/  {password, current_password?} -> set or change (signed in)
Reset     : POST /auth/forgot/ + /auth/reset/             -> emailed link flow
Session   : GET/PATCH /auth/me/ + POST /auth/refresh/

Accounts created through OTP-only or Google have no password until one is set.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from google.auth.transport import requests as g_requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from . import otp
from .models import EmailOTP

User = get_user_model()
log = logging.getLogger(__name__)


# ---------------- helpers ----------------
def user_data(user):
    return {
        'id': user.id,
        'name': user.display_name,
        'email': user.email,
        'is_staff': user.is_staff,
        'has_password': user.has_usable_password(),
        'profile_picture': user.profile_picture or '',
    }


def tokens_for(user, created=False):
    refresh = RefreshToken.for_user(user)
    return {
        'user': user_data(user),
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'created': created,
    }


def _email(request):
    return (request.data.get('email') or '').strip().lower()


def _password_error(request):
    """Validate an optional password. Returns an error message or None."""
    password = request.data.get('password') or ''
    if not password:
        return None, ''
    try:
        validate_password(password)
    except ValidationError as e:
        return None, ' '.join(e.messages)
    return password, None


def _send_or_fail(email, code, purpose, name=''):
    """Email the code. Returns an error Response, or None when sent."""
    try:
        otp.send_code(email, code, purpose, name)
    except Exception:
        EmailOTP.objects.filter(email=email, purpose=purpose).delete()
        log.exception('Could not send %s code to %s', purpose, email)
        return Response({'detail': 'We could not send the code email. Please try again shortly.'}, status=502)
    return None


class Public(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []


# ---------------- Sign up: details -> emailed code -> account ----------------
class RegisterView(Public):
    """Step 1. Password is optional — members can live on email codes only."""

    def post(self, request):
        name = (request.data.get('name') or '').strip()
        email = _email(request)
        password, pw_error = _password_error(request)
        if not name or not email:
            return Response({'detail': 'Name and email are required.'}, status=400)
        if pw_error:
            return Response({'detail': pw_error}, status=400)
        if User.objects.filter(email__iexact=email).exists():
            return Response({'detail': 'An account with this email already exists. Please log in.'}, status=400)
        if otp.cooling_down(email, EmailOTP.SIGNUP):
            return Response({'detail': 'Please wait a minute before requesting another code.'}, status=429)
        code = otp.issue_code(
            email, EmailOTP.SIGNUP, name=name[:120],
            password_hash=make_password(password) if password else '',
        )
        error = _send_or_fail(email, code, EmailOTP.SIGNUP, name)
        return error or Response({'pending': True, 'email': email})


class VerifySignupView(Public):
    """Step 2. Right code -> the account is created and the person is signed in."""

    def post(self, request):
        email = _email(request)
        record, error = otp.check_code(email, EmailOTP.SIGNUP, request.data.get('code'))
        if error:
            return Response({'detail': error}, status=400)
        if User.objects.filter(email__iexact=email).exists():
            record.delete()
            return Response({'detail': 'An account with this email already exists. Please log in.'}, status=400)
        user = User.objects.create(email=email, first_name=record.name)
        if record.password_hash:
            user.password = record.password_hash
        else:
            user.set_unusable_password()
        user.save()
        record.delete()
        return Response(tokens_for(user, created=True), status=status.HTTP_201_CREATED)


# ---------------- Log in ----------------
class LoginView(Public):
    """Password login — only works for accounts that set a password."""

    def post(self, request):
        email = _email(request)
        password = request.data.get('password') or ''
        user = User.objects.filter(email__iexact=email).first()
        if not user or not user.is_active or not user.check_password(password):
            return Response({'detail': 'Incorrect email or password.'}, status=401)
        return Response(tokens_for(user))


class LoginCodeRequestView(Public):
    """Passwordless login. Always answers 200 so it cannot be used to find out who has an account."""

    def post(self, request):
        email = _email(request)
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user and not otp.cooling_down(email, EmailOTP.LOGIN):
            code = otp.issue_code(email, EmailOTP.LOGIN)
            error = _send_or_fail(email, code, EmailOTP.LOGIN, user.display_name)
            if error:
                return error
        return Response({'detail': 'If that email has an account, a code is on its way.'})


class LoginCodeVerifyView(Public):
    def post(self, request):
        email = _email(request)
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        record, error = otp.check_code(email, EmailOTP.LOGIN, request.data.get('code'))
        if error or not user:
            return Response({'detail': error or 'That code is not correct.'}, status=400)
        record.delete()
        return Response(tokens_for(user))


# ---------------- Google ----------------
class GoogleLoginView(Public):
    """Verifies the Google ID token from the browser; signs in or creates the account."""

    def post(self, request):
        if not settings.GOOGLE_CLIENT_ID:
            return Response({'detail': 'Google sign-in is not configured yet.'}, status=503)
        credential = request.data.get('credential') or ''
        if not credential:
            return Response({'detail': 'Google credential is required.'}, status=400)
        try:
            info = id_token.verify_oauth2_token(credential, g_requests.Request(), settings.GOOGLE_CLIENT_ID)
        except Exception as e:
            log.warning('Google token verification failed: %s', e)
            return Response({'detail': 'Google sign-in failed. Please try again.'}, status=401)
        email = (info.get('email') or '').lower()
        if not email or not info.get('email_verified'):
            return Response({'detail': 'Your Google email is not verified.'}, status=401)
        user = User.objects.filter(email__iexact=email).first()
        created = user is None
        if created:
            user = User(
                email=email,
                first_name=(info.get('name') or email.split('@')[0])[:120],
                profile_picture=info.get('picture') or '',
            )
            user.set_unusable_password()
            user.save()
        elif not user.is_active:
            return Response({'detail': 'This account is disabled.'}, status=403)
        return Response(tokens_for(user, created=created))


# ---------------- Password (optional) ----------------
class SetPasswordView(APIView):
    """Signed-in members can set or change their password.

    Accounts that already have a password must send `current_password`.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        password, pw_error = _password_error(request)
        if pw_error:
            return Response({'detail': pw_error}, status=400)
        if not password:
            return Response({'detail': 'Password is required.'}, status=400)
        user = request.user
        if user.has_usable_password():
            current = request.data.get('current_password') or ''
            if not user.check_password(current):
                return Response({'detail': 'Your current password is not correct.'}, status=400)
        user.set_password(password)
        user.save()
        return Response({'detail': 'Password updated. You can now sign in with it too.'})


# ---------------- Password reset ----------------
class ForgotPasswordView(Public):
    """Always answers 200 so the form cannot be used to discover which emails have accounts."""

    def post(self, request):
        try:
            user = User.objects.filter(email__iexact=_email(request), is_active=True).first()
            if user and user.has_usable_password():
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                link = f'{settings.RESET_PASSWORD_URL or settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}'
                send_mail(
                    'Reset your password',
                    f'Hello {user.display_name},\n\nUse this link to choose a new password (valid for 3 days):\n{link}\n\n'
                    'If you did not ask for this, you can ignore this email.\n\n'
                    'Richard Kwanya Snr #Babawa\n',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            return Response({'detail': 'If that email has an account, a reset link is on its way.'})
        except Exception:
            log.exception('Password reset failed')
            return Response({'detail': 'Something went wrong. Please try again.'}, status=500)


class ResetPasswordView(Public):
    def post(self, request):
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(request.data.get('uid') or '')))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None
        if not user or not default_token_generator.check_token(user, request.data.get('token') or ''):
            return Response({'detail': 'This reset link is invalid or has expired.'}, status=400)
        password = request.data.get('password') or ''
        try:
            validate_password(password, user)
        except ValidationError as e:
            return Response({'detail': ' '.join(e.messages)}, status=400)
        user.set_password(password)
        user.save()
        return Response({'detail': 'Password updated. You can sign in now.'})


# ---------------- Session ----------------
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(user_data(request.user))

    def patch(self, request):
        user = request.user
        if 'profile_picture' in request.data:
            user.profile_picture = request.data['profile_picture']
            user.save()
        return Response(user_data(user))
