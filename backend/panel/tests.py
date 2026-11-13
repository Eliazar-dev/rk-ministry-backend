import hashlib

import cloudinary
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from content.models import Album, Comment, Devotional, HeroSlide, PastorProfile, PrayerRequest, Sermon, video_poster
from shop.models import Order, OrderItem, Product

User = get_user_model()
BASE = '/api/manage'


class PanelBase(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user('boss@example.com', 'pw123456', first_name='Boss', is_staff=True)
        self.member = User.objects.create_user('mem@example.com', 'pw123456', first_name='Mem')

    def as_staff(self):
        self.client.force_authenticate(self.staff)

    def as_member(self):
        self.client.force_authenticate(self.member)


class AccessTests(PanelBase):
    def test_anonymous_and_members_are_refused(self):
        """Test all admin endpoints return 401 for anonymous and 403 for non-staff."""
        # GET-only endpoints
        get_only = ['/stats/', '/pastor/']
        # CRUD endpoints
        crud = ['/hero/', '/sermons/', '/lessons/', '/devotionals/', '/articles/', '/albums/', '/products/']
        # Read-only endpoints
        read_only = ['/orders/', '/donations/', '/members/', '/prayers/', '/messages/', '/comments/']
        # POST-only
        post_only = ['/upload-sign/']

        all_endpoints = get_only + crud + read_only + post_only

        # Anonymous: 401 for all methods
        for path in all_endpoints:
            self.assertEqual(self.client.get(BASE + path).status_code, 401, f'GET {path} should be 401 for anonymous')
        for path in crud + post_only:
            self.assertEqual(self.client.post(BASE + path, {}).status_code, 401, f'POST {path} should be 401 for anonymous')
        for path in crud:
            self.assertEqual(self.client.patch(BASE + path + '1/', {}).status_code, 401, f'PATCH {path} should be 401 for anonymous')
            self.assertEqual(self.client.delete(BASE + path + '1/').status_code, 401, f'DELETE {path} should be 401 for anonymous')

        # Non-staff member: 403 for all methods
        self.as_member()
        for path in all_endpoints:
            self.assertEqual(self.client.get(BASE + path).status_code, 403, f'GET {path} should be 403 for non-staff')
        for path in crud + post_only:
            self.assertEqual(self.client.post(BASE + path, {}).status_code, 403, f'POST {path} should be 403 for non-staff')
        for path in crud:
            self.assertEqual(self.client.patch(BASE + path + '1/', {}).status_code, 403, f'PATCH {path} should be 403 for non-staff')
            self.assertEqual(self.client.delete(BASE + path + '1/').status_code, 403, f'DELETE {path} should be 403 for non-staff')

        # Staff: 200 for GET (except POST-only endpoints), 201/200 for POST/PATCH
        self.as_staff()
        for path in get_only + crud + read_only:
            res = self.client.get(BASE + path)
            self.assertIn(res.status_code, [200, 404], f'GET {path} should be 200 or 404 for staff')
        # POST-only endpoint
        res = self.client.post(BASE + '/upload-sign/', {})
        self.assertEqual(res.status_code, 503, 'POST /upload-sign/ should be 503 (Cloudinary not configured)')

    def test_login_payload_tells_the_site_who_is_staff(self):
        res = self.client.post('/api/auth/login/', {'email': 'boss@example.com', 'password': 'pw123456'}, format='json')
        self.assertTrue(res.data['user']['is_staff'])
        res = self.client.post('/api/auth/login/', {'email': 'mem@example.com', 'password': 'pw123456'}, format='json')
        self.assertFalse(res.data['user']['is_staff'])


class ContentCrudTests(PanelBase):
    def setUp(self):
        super().setUp()
        self.as_staff()

    def test_create_sermon_with_uploaded_cover_url(self):
        res = self.client.post(BASE + '/sermons/', {
            'title': 'Hope', 'youtube_url': 'https://youtu.be/aqz-KE-bpKQ',
            'cover_url': 'https://res.cloudinary.com/x/image/upload/a.jpg',
        }, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['cover_src'], 'https://res.cloudinary.com/x/image/upload/a.jpg')
        self.assertNotIn('cover', res.data)  # raw upload column is hidden
        self.assertTrue(Sermon.objects.get(pk=res.data['id']).published)

    def test_saving_a_url_clears_an_older_upload(self):
        s = Sermon.objects.create(title='T', youtube_url='https://youtu.be/aqz-KE-bpKQ', cover='rk/covers/old')
        res = self.client.patch(f'{BASE}/sermons/{s.pk}/', {'cover_url': 'https://img.example.com/new.jpg'}, format='json')
        self.assertEqual(res.status_code, 200)
        s.refresh_from_db()
        self.assertFalse(s.cover)
        self.assertEqual(s.cover_src, 'https://img.example.com/new.jpg')

    def test_toggle_published_hides_it_from_the_public_api(self):
        s = Sermon.objects.create(title='T', youtube_url='https://youtu.be/aqz-KE-bpKQ')
        self.assertEqual(len(self.client.get('/api/sermons/').data), 1)
        self.client.patch(f'{BASE}/sermons/{s.pk}/', {'published': False}, format='json')
        self.assertEqual(len(self.client.get('/api/sermons/').data), 0)

    def test_lists_are_paginated_searchable_and_light(self):
        for i in range(25):
            Devotional.objects.create(title=f'Devo {i}', body='long body text')
        res = self.client.get(BASE + '/devotionals/')
        self.assertEqual(res.data['count'], 25)
        self.assertEqual(len(res.data['results']), 20)
        self.assertNotIn('body', res.data['results'][0])
        one = self.client.get(f"{BASE}/devotionals/{res.data['results'][0]['id']}/")
        self.assertIn('body', one.data)
        self.assertEqual(self.client.get(BASE + '/devotionals/?q=Devo 24').data['count'], 1)

    def test_album_link_must_be_https(self):
        bad = self.client.post(BASE + '/albums/', {'title': 'Mission', 'photos_url': 'http://insecure.example.com/a'}, format='json')
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post(BASE + '/albums/', {'title': 'Mission', 'photos_url': 'https://x.pixieset.com/a'}, format='json')
        self.assertEqual(ok.status_code, 201, ok.data)
        self.assertEqual(Album.objects.count(), 1)

    def test_articles_filter_by_section(self):
        self.client.post(BASE + '/articles/', {'section': 'blog', 'title': 'B'}, format='json')
        self.client.post(BASE + '/articles/', {'section': 'ebook', 'title': 'E'}, format='json')
        self.assertEqual(self.client.get(BASE + '/articles/?section=ebook').data['count'], 1)

    def test_hero_slides_and_auto_poster(self):
        res = self.client.post(BASE + '/hero/', {'title': 'One', 'video_url': 'https://res.cloudinary.com/d/video/upload/v1/clip.mp4', 'order': 1}, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        pub = {h['id']: h for h in self.client.get('/api/hero/').data}
        self.assertEqual(pub[res.data['id']]['poster'], 'https://res.cloudinary.com/d/video/upload/so_1,c_limit,w_1280,q_auto/v1/clip.jpg')
        self.assertEqual(video_poster('https://example.com/a.mp4'), '')

    def test_pastor_profile_is_a_single_record(self):
        self.assertEqual(self.client.get(BASE + '/pastor/').data, {})
        self.client.put(BASE + '/pastor/', {'name': 'Richard Kwanya Snr', 'biography': 'One\n\nTwo'}, format='json')
        self.client.put(BASE + '/pastor/', {'title': 'Evangelist'}, format='json')
        self.assertEqual(PastorProfile.objects.count(), 1)
        self.assertEqual(self.client.get('/api/about/').data['title'], 'Evangelist')
        self.assertEqual(self.client.get('/api/about/').data['biography'], 'One\n\nTwo')


class InboxAndMoneyTests(PanelBase):
    def setUp(self):
        super().setUp()
        self.as_staff()

    def test_comment_moderation(self):
        s = Sermon.objects.create(title='Faith talk', youtube_url='https://youtu.be/aqz-KE-bpKQ')
        c = Comment.objects.create(user=self.member, kind='sermon', object_id=s.pk, text='Amen')
        res = self.client.get(BASE + '/comments/')
        self.assertEqual(res.data['results'][0]['target'], 'Faith talk')
        self.assertEqual(res.data['results'][0]['member'], 'Mem')
        self.client.patch(f'{BASE}/comments/{c.pk}/', {'approved': False}, format='json')
        self.assertEqual(len(self.client.get(f'/api/engage/sermon/{s.pk}/').data['comments']), 0)
        self.assertEqual(self.client.patch(f'{BASE}/comments/{c.pk}/', {'text': 'edited'}, format='json').data['text'], 'Amen')

    def test_prayer_requests_can_be_marked_prayed_for(self):
        p = PrayerRequest.objects.create(name='A', email='a@example.com', request='Pray')
        self.client.patch(f'{BASE}/prayers/{p.pk}/', {'prayed_for': True}, format='json')
        p.refresh_from_db()
        self.assertTrue(p.prayed_for)
        self.assertEqual(self.client.post(BASE + '/prayers/', {}, format='json').status_code, 405)

    def test_orders_are_read_only_but_can_be_marked_paid(self):
        prod = Product.objects.create(name='Mug', price=700, description='d')
        o = Order.objects.create(user=self.member, name='Mem', email='mem@example.com', location='Eldoret', phone='254712345678', amount=700)
        OrderItem.objects.create(order=o, product=prod, name='Mug', price=700, qty=1)
        res = self.client.get(BASE + '/orders/')
        self.assertEqual(res.data['results'][0]['items'][0]['name'], 'Mug')
        self.assertEqual(self.client.delete(f'{BASE}/orders/{o.pk}/').status_code, 405)
        done = self.client.post(f'{BASE}/orders/{o.pk}/mark-paid/', {'receipt': 'QWE123'}, format='json')
        self.assertEqual(done.data['status'], 'paid')
        self.assertEqual(done.data['mpesa_receipt'], 'QWE123')

    def test_dashboard_numbers(self):
        o = Order.objects.create(user=self.member, name='Mem', email='m@example.com', location='x', phone='254712345678', amount=1500, status='paid')
        Order.objects.create(user=self.member, name='Mem', email='m@example.com', location='x', phone='254712345678', amount=900)
        data = self.client.get(BASE + '/stats/').data
        self.assertEqual(data['orders']['revenue'], 1500)
        self.assertEqual(data['orders']['pending'], 1)
        self.assertEqual(data['members'], 2)
        self.assertEqual(len(data['series']), 14)
        self.assertEqual(data['series'][-1]['orders'], 1500)
        self.assertTrue(o.pk)

    def test_members_can_be_switched_off_not_deleted(self):
        self.assertEqual(self.client.delete(f'{BASE}/members/{self.member.pk}/').status_code, 405)
        self.client.patch(f'{BASE}/members/{self.member.pk}/', {'is_active': False}, format='json')
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)


class UploadSignTests(PanelBase):
    def test_signature_matches_cloudinary_rules(self):
        cloudinary.config(cloud_name='demo', api_key='123', api_secret='sekret')
        self.as_staff()
        res = self.client.post(BASE + '/upload-sign/', {'folder': 'covers', 'type': 'image'}, format='json')
        self.assertEqual(res.status_code, 200, res.data)
        expect = hashlib.sha1(f"folder=rk/covers&timestamp={res.data['timestamp']}sekret".encode()).hexdigest()
        self.assertEqual(res.data['signature'], expect)
        self.assertEqual(res.data['upload_url'], 'https://api.cloudinary.com/v1_1/demo/image/upload')
        self.assertEqual(self.client.post(BASE + '/upload-sign/', {'folder': '../etc'}, format='json').status_code, 400)

    def test_clear_message_when_cloudinary_is_not_configured(self):
        cloudinary.config(cloud_name='', api_key='', api_secret='')
        self.as_staff()
        res = self.client.post(BASE + '/upload-sign/', {}, format='json')
        self.assertEqual(res.status_code, 503)
        self.assertIn('CLOUDINARY_URL', res.data['detail'])
