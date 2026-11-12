"""Email one-time codes: issue, send, check. Codes live 10 minutes, 5 wrong tries, 30 s resend cooldown."""
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac

from .models import EmailOTP

TTL = timedelta(minutes=10)
COOLDOWN = timedelta(seconds=30)
MAX_ATTEMPTS = 5


def _hash(email, purpose, code):
    return salted_hmac('rk.otp', f'{email}|{purpose}|{code}').hexdigest()


def cooling_down(email, purpose):
    last = EmailOTP.objects.filter(email=email, purpose=purpose).order_by('-created').first()
    return bool(last and timezone.now() - last.created < COOLDOWN)


def issue_code(email, purpose, name='', password_hash=''):
    """Replace any previous code for this email+purpose and return the new plain code."""
    EmailOTP.objects.filter(email=email, purpose=purpose).delete()
    code = f'{secrets.randbelow(10**6):06d}'
    EmailOTP.objects.create(
        email=email, purpose=purpose, code_hash=_hash(email, purpose, code), name=name, password_hash=password_hash
    )
    return code


def send_code(email, code, purpose, name=''):
    greeting = f'Hello {name},' if name else 'Hello,'
    action = 'complete your registration' if purpose == EmailOTP.SIGNUP else 'sign in to your account'
    site_name = getattr(settings, 'SITE_NAME', 'Richard Kwanya Snr Ministry')
    send_mail(
        f'Your verification code for {site_name}',
        f'{greeting}\n\n'
        f'Thank you for choosing {site_name}. Your verification code to {action} is:\n\n'
        f'    {code}\n\n'
        f'This code will expire in 10 minutes for your security.\n\n'
        f'If you did not request this code, please disregard this email. Your account remains safe.\n\n'
        f'Blessings,\n'
        f'{site_name}\n'
        f'Richard Kwanya Snr #Babawa\n',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def check_code(email, purpose, code):
    """Returns (otp, None) when the code is right, else (None, message). Wrong guesses are counted."""
    otp = EmailOTP.objects.filter(email=email, purpose=purpose).first()
    if not otp:
        return None, 'No code was requested for this email. Please request a new one.'
    if timezone.now() - otp.created > TTL:
        otp.delete()
        return None, 'This code has expired. Please request a new one.'
    if otp.attempts >= MAX_ATTEMPTS:
        otp.delete()
        return None, 'Too many wrong attempts. Please request a new code.'
    if not constant_time_compare(otp.code_hash, _hash(email, purpose, str(code).strip())):
        otp.attempts += 1
        otp.save(update_fields=['attempts'])
        return None, 'That code is not correct.'
    return otp, None
