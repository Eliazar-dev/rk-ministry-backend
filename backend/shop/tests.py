from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from content.models import Comment, Sermon
from shop.models import Order, Product


class ApiFlowTests(TestCase):
    def setUp(self):
        self.c = APIClient()

    def signup(self):
        """Create the member directly (the OTP signup flow has its own tests in accounts/tests.py) and log in."""
        from accounts.models import User
        User.objects.create_user(email='jane@x.com', password='secret123', first_name='Jane Doe')
        r = self.c.post('/api/auth/login/', {'email': 'jane@x.com', 'password': 'secret123'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.c.credentials(HTTP_AUTHORIZATION='Bearer ' + r.data['access'])
        return r.data

    def test_public_lists_hide_protected_fields(self):
        from content.models import Album, Article, Devotional, Lesson
        Sermon.objects.create(title='Hope', youtube_url='https://youtu.be/aqz-KE-bpKQ')
        Lesson.objects.create(title='L', quarter='Q4', date_range='a', youtube_url='https://youtu.be/x', pdf_url='https://x/l.pdf')
        Devotional.objects.create(title='D', body='secret body text')
        Article.objects.create(section='blog', title='B', body='secret article', pdf_url='https://x/b.pdf')
        Album.objects.create(title='Crusade', photos_url='https://pixieset.example/album')
        hidden = {'/api/sermons/': ['youtube'], '/api/lessons/': ['youtube', 'pdf'], '/api/devotionals/': ['body'],
                  '/api/blogs/': ['body', 'pdf'], '/api/gallery/': ['link']}
        for url, fields in hidden.items():
            r = self.c.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertTrue(r.data[0]['locked'], url)
            for f in fields:
                self.assertNotIn(f, r.data[0], f'{url} leaked {f}')
        self.assertFalse(self.c.get('/api/lessons/').data[0]['hasPdf'])  # hasPdf is false for anonymous users
        for url in ['/api/hero/', '/api/products/', '/api/about/']:
            self.assertEqual(self.c.get(url).status_code, 200, url)
        self.signup()
        for url, fields in hidden.items():
            r = self.c.get(url)
            self.assertFalse(r.data[0]['locked'], url)
            for f in fields:
                self.assertIn(f, r.data[0], url)
        self.assertEqual(self.c.get('/api/gallery/').data[0]['link'], 'https://pixieset.example/album')
        self.assertTrue(self.c.get('/api/lessons/').data[0]['hasPdf'])  # hasPdf is true for authenticated users

    def test_member_actions_still_need_an_account(self):
        for method, url in [('post', '/api/orders/'), ('post', '/api/donations/'), ('get', '/api/auth/me/'),
                            ('get', '/api/engage/sermon/1/'), ('post', '/api/engage/sermon/1/like/')]:
            self.assertEqual(getattr(self.c, method)(url).status_code, 401, url)

    def test_stale_token_does_not_break_public_pages(self):
        Sermon.objects.create(title='Hope', youtube_url='https://youtu.be/x')
        self.c.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')
        r = self.c.get('/api/sermons/')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data[0]['locked'])

    def test_album_link_must_be_https(self):
        from django.core.exceptions import ValidationError
        from content.models import Album
        a = Album(title='x', photos_url='http://insecure.example/a')
        with self.assertRaises(ValidationError):
            a.full_clean(exclude=['cover', 'cover_url'])

    def test_pastor_profile_endpoint(self):
        from content.models import PastorProfile
        self.assertEqual(self.c.get('/api/about/').data, {})
        PastorProfile.objects.create(short_intro='Hi', biography='One\n\nTwo', photo_url='https://x/p.jpg')
        d = self.c.get('/api/about/').data
        self.assertEqual((d['name'], d['intro'], d['photo']), ('Richard Kwanya Snr', 'Hi', 'https://x/p.jpg'))

    def test_forms_open_to_visitors_with_honeypot(self):
        from content.models import ContactMessage, PrayerRequest
        r = self.c.post('/api/prayer-requests/', {'name': 'A', 'email': 'a@x.com', 'request': 'Pray'}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(PrayerRequest.objects.count(), 1)
        bot = self.c.post('/api/contact/', {'name': 'B', 'email': 'b@x.com', 'message': 'spam', 'website': 'http://spam'}, format='json')
        self.assertEqual(bot.status_code, 201)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_forms_are_rate_limited(self):
        from django.core.cache import cache
        cache.clear()
        codes = [self.c.post('/api/contact/', {'name': 'A', 'email': 'a@x.com', 'message': 'hi'}, format='json').status_code
                 for _ in range(12)]
        self.assertIn(429, codes)
        cache.clear()

    def test_status_page_and_health(self):
        r = self.c.get('/health/')
        self.assertEqual((r.status_code, r.json()['status']), (200, 'ok'))
        page = self.c.get('/')
        self.assertContains(page, 'Backend running')
        detail = self.c.get('/health/?detail=1').json()
        self.assertIn('24h', detail['uptime'])

    def test_default_carousel_videos_exist(self):
        r = self.c.get('/api/hero/')
        self.assertEqual(len(r.data), 2)
        self.assertIn('HOPE-TO-THE-HOPELESS', r.data[0]['video'])

    def test_register_login_duplicate(self):
        self.signup()
        dup = APIClient().post('/api/auth/register/', {'name': 'J', 'email': 'JANE@x.com', 'password': 'secret123'}, format='json')
        self.assertEqual(dup.status_code, 400)
        bad = APIClient().post('/api/auth/login/', {'email': 'jane@x.com', 'password': 'nope'}, format='json')
        self.assertEqual(bad.status_code, 401)
        ok = APIClient().post('/api/auth/login/', {'email': 'jane@x.com', 'password': 'secret123'}, format='json')
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.data['user']['name'], 'Jane Doe')

    def test_password_reset_flow(self):
        self.signup()
        anon = APIClient()
        # unknown email still answers 200 and sends nothing
        self.assertEqual(anon.post('/api/auth/forgot/', {'email': 'ghost@x.com'}, format='json').status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(anon.post('/api/auth/forgot/', {'email': 'jane@x.com'}, format='json').status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        import re
        m = re.search(r'uid=([^&\s]+)&token=([^\s]+)', mail.outbox[0].body)
        uid, token = m.group(1), m.group(2)
        bad = anon.post('/api/auth/reset/', {'uid': uid, 'token': 'wrong', 'password': 'newpass123'}, format='json')
        self.assertEqual(bad.status_code, 400)
        ok = anon.post('/api/auth/reset/', {'uid': uid, 'token': token, 'password': 'newpass123'}, format='json')
        self.assertEqual(ok.status_code, 200)
        login = anon.post('/api/auth/login/', {'email': 'jane@x.com', 'password': 'newpass123'}, format='json')
        self.assertEqual(login.status_code, 200)
        # the link cannot be reused
        again = anon.post('/api/auth/reset/', {'uid': uid, 'token': token, 'password': 'another123'}, format='json')
        self.assertEqual(again.status_code, 400)

    def test_content_likes_comments(self):
        self.signup()
        s = Sermon.objects.create(title='Hope', youtube_url='https://youtu.be/aqz-KE-bpKQ', cover_url='https://x/y.jpg')
        data = self.c.get('/api/sermons/').data
        self.assertEqual(data[0]['youtube'], 'https://youtu.be/aqz-KE-bpKQ')
        self.assertEqual(data[0]['cover'], 'https://x/y.jpg')
        r = self.c.post(f'/api/engage/sermon/{s.id}/like/')
        self.assertEqual((r.data['likes'], r.data['liked']), (1, True))
        r = self.c.post(f'/api/engage/sermon/{s.id}/like/')
        self.assertEqual((r.data['likes'], r.data['liked']), (0, False))
        r = self.c.post(f'/api/engage/sermon/{s.id}/comments/', {'text': 'Amen'}, format='json')
        self.assertEqual(r.data['comments'][0]['text'], 'Amen')
        Comment.objects.update(approved=False)  # admin hides it
        self.assertEqual(self.c.get(f'/api/engage/sermon/{s.id}/').data['comments'], [])

    def test_order_payment_and_email(self):
        self.signup()
        p = Product.objects.create(name='Bible', price=2500, description='d', image_url='https://x/i.jpg')
        bad = self.c.post('/api/orders/', {'name': 'J', 'email': 'j@x.com', 'location': 'Thika', 'phone': '123', 'items': [{'id': p.id, 'qty': 1}]}, format='json')
        self.assertEqual(bad.status_code, 400)
        r = self.c.post('/api/orders/', {
            'name': 'Jane Doe', 'email': 'jane@x.com', 'location': 'Thika', 'phone': '0712 345 678',
            'items': [{'id': p.id, 'qty': 2, 'price': 1}],  # client price is ignored
        }, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['amount'], 5000)
        oid = r.data['id']
        self.assertEqual(self.c.get(f'/api/orders/{oid}/').data['status'], 'pending')
        Order.objects.filter(pk=oid).update(created=timezone.now() - timedelta(seconds=30))
        self.assertEqual(self.c.get(f'/api/orders/{oid}/').data['status'], 'paid')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Order', mail.outbox[0].subject)

    def test_mpesa_callback_marks_paid_and_failed(self):
        self.signup()
        r = self.c.post('/api/donations/', {'amount': 500, 'phone': '254712345678'}, format='json')
        self.assertEqual(r.status_code, 201)
        from shop.models import Donation
        d = Donation.objects.get(pk=r.data['id'])
        d.checkout_request_id = 'ws_CO_123'
        d.save()
        anon = APIClient()
        cb = {'Body': {'stkCallback': {'CheckoutRequestID': 'ws_CO_123', 'ResultCode': 0,
              'CallbackMetadata': {'Item': [{'Name': 'MpesaReceiptNumber', 'Value': 'QWE123'}]}}}}
        self.assertEqual(anon.post('/api/mpesa/callback/', cb, format='json').status_code, 200)
        d.refresh_from_db()
        self.assertEqual((d.status, d.mpesa_receipt), ('paid', 'QWE123'))
