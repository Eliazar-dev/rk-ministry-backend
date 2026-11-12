import re
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from .models import EmailOTP, User

SIGNUP = {'name': 'Jane Doe', 'email': 'jane@x.com', 'password': 'secret123'}


def last_code():
    return re.search(r'\b(\d{6})\b', mail.outbox[-1].body).group(1)


class OtpSignupTests(TestCase):
    def setUp(self):
        self.c = APIClient()

    def test_signup_needs_the_emailed_code(self):
        r = self.c.post('/api/auth/register/', SIGNUP, format='json')
        self.assertEqual((r.status_code, r.data['pending']), (200, True))
        self.assertNotIn('access', r.data)
        self.assertFalse(User.objects.exists())  # nothing created until verified
        self.assertEqual(self.c.post('/api/auth/login/', SIGNUP, format='json').status_code, 401)
        self.assertEqual(len(mail.outbox), 1)
        # code is only stored hashed
        self.assertNotIn(last_code(), EmailOTP.objects.get().code_hash)

        wrong = self.c.post('/api/auth/verify/', {'email': 'jane@x.com', 'code': '000000'}, format='json')
        self.assertEqual(wrong.status_code, 400)
        ok = self.c.post('/api/auth/verify/', {'email': 'JANE@x.com', 'code': last_code()}, format='json')
        self.assertEqual(ok.status_code, 201)
        self.assertTrue(ok.data['created'])
        self.assertEqual(ok.data['user']['name'], 'Jane Doe')
        self.assertTrue(User.objects.get().check_password('secret123'))
        self.assertFalse(EmailOTP.objects.exists())
        # code cannot be replayed
        again = self.c.post('/api/auth/verify/', {'email': 'jane@x.com', 'code': last_code()}, format='json')
        self.assertEqual(again.status_code, 400)

    def test_existing_email_and_weak_password_rejected(self):
        User.objects.create_user(email='jane@x.com', password='secret123', first_name='J')
        self.assertEqual(self.c.post('/api/auth/register/', SIGNUP, format='json').status_code, 400)
        weak = {**SIGNUP, 'email': 'new@x.com', 'password': '123'}
        self.assertEqual(self.c.post('/api/auth/register/', weak, format='json').status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_lockout_after_five_wrong_guesses(self):
        self.c.post('/api/auth/register/', SIGNUP, format='json')
        good = last_code()
        for _ in range(5):
            r = self.c.post('/api/auth/verify/', {'email': 'jane@x.com', 'code': '999999' if good != '999999' else '111111'}, format='json')
            self.assertEqual(r.status_code, 400)
        late = self.c.post('/api/auth/verify/', {'email': 'jane@x.com', 'code': good}, format='json')
        self.assertEqual(late.status_code, 400)  # even the right code is refused now
        self.assertFalse(User.objects.exists())

    def test_expired_code(self):
        self.c.post('/api/auth/register/', SIGNUP, format='json')
        EmailOTP.objects.update(created=timezone.now() - timedelta(minutes=11))
        r = self.c.post('/api/auth/verify/', {'email': 'jane@x.com', 'code': last_code()}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('expired', r.data['detail'])

    def test_resend_cooldown_then_new_code_replaces_old(self):
        self.c.post('/api/auth/register/', SIGNUP, format='json')
        old = last_code()
        self.assertEqual(self.c.post('/api/auth/register/', SIGNUP, format='json').status_code, 429)
        EmailOTP.objects.update(created=timezone.now() - timedelta(seconds=31))
        self.assertEqual(self.c.post('/api/auth/register/', SIGNUP, format='json').status_code, 200)
        self.assertEqual(EmailOTP.objects.count(), 1)
        new = last_code()
        if new != old:  # (1 in a million they match)
            bad = self.c.post('/api/auth/verify/', {'email': 'jane@x.com', 'code': old}, format='json')
            self.assertEqual(bad.status_code, 400)


class OtpLoginTests(TestCase):
    def setUp(self):
        self.c = APIClient()
        User.objects.create_user(email='jane@x.com', password='secret123', first_name='Jane Doe')

    def test_login_with_emailed_code(self):
        r = self.c.post('/api/auth/otp/request/', {'email': 'jane@x.com'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        ok = self.c.post('/api/auth/otp/login/', {'email': 'jane@x.com', 'code': last_code()}, format='json')
        self.assertEqual(ok.status_code, 200)
        self.assertFalse(ok.data['created'])
        self.assertIn('access', ok.data)

    def test_unknown_email_gets_same_answer_and_no_email(self):
        r = self.c.post('/api/auth/otp/request/', {'email': 'ghost@x.com'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        bad = self.c.post('/api/auth/otp/login/', {'email': 'ghost@x.com', 'code': '123456'}, format='json')
        self.assertEqual(bad.status_code, 400)

    def test_signup_code_cannot_be_used_to_log_in(self):
        self.c.post('/api/auth/register/', {'name': 'N', 'email': 'new@x.com', 'password': 'secret123'}, format='json')
        r = self.c.post('/api/auth/otp/login/', {'email': 'new@x.com', 'code': last_code()}, format='json')
        self.assertEqual(r.status_code, 400)


@override_settings(GOOGLE_CLIENT_ID='test-client-id')
class GoogleTests(TestCase):
    def setUp(self):
        self.c = APIClient()

    @patch('accounts.views.id_token.verify_oauth2_token')
    def test_google_creates_then_reuses_account(self, verify):
        verify.return_value = {'email': 'Grace@Gmail.com', 'email_verified': True, 'name': 'Grace Wanjiru'}
        first = self.c.post('/api/auth/google/', {'credential': 'tok'}, format='json')
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.data['created'])
        self.assertEqual(first.data['user'], {'id': first.data['user']['id'], 'name': 'Grace Wanjiru', 'email': 'grace@gmail.com', 'is_staff': False})
        self.assertFalse(User.objects.get().has_usable_password())
        second = self.c.post('/api/auth/google/', {'credential': 'tok'}, format='json')
        self.assertFalse(second.data['created'])
        self.assertEqual(User.objects.count(), 1)
        # the audience is always our own client id
        self.assertEqual(verify.call_args[0][2], 'test-client-id')

    @patch('accounts.views.id_token.verify_oauth2_token')
    def test_google_links_to_existing_email_account(self, verify):
        User.objects.create_user(email='jane@x.com', password='secret123', first_name='Jane')
        verify.return_value = {'email': 'jane@x.com', 'email_verified': True, 'name': 'Someone Else'}
        r = self.c.post('/api/auth/google/', {'credential': 'tok'}, format='json')
        self.assertEqual((r.status_code, r.data['created'], r.data['user']['name']), (200, False, 'Jane'))

    @patch('accounts.views.id_token.verify_oauth2_token')
    def test_google_rejects_unverified_email_and_bad_token(self, verify):
        verify.return_value = {'email': 'a@x.com', 'email_verified': False}
        self.assertEqual(self.c.post('/api/auth/google/', {'credential': 't'}, format='json').status_code, 401)
        verify.side_effect = ValueError('bad token')
        self.assertEqual(self.c.post('/api/auth/google/', {'credential': 't'}, format='json').status_code, 401)
        self.assertFalse(User.objects.exists())

    @override_settings(GOOGLE_CLIENT_ID='')
    def test_google_not_configured(self):
        self.assertEqual(self.c.post('/api/auth/google/', {'credential': 't'}, format='json').status_code, 503)
