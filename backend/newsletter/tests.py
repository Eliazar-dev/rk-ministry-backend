from django.test import TestCase
from .models import NewsletterSubscriber


class NewsletterTests(TestCase):
    def test_subscribe_new(self):
        resp = self.client.post('/api/newsletter/subscribe/', {'email': 'test@example.com', 'name': 'Test User'})
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(NewsletterSubscriber.objects.filter(email='test@example.com', active=True).exists())

    def test_subscribe_existing(self):
        NewsletterSubscriber.objects.create(email='test@example.com', name='Test User', active=True)
        resp = self.client.post('/api/newsletter/subscribe/', {'email': 'test@example.com'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(NewsletterSubscriber.objects.filter(email='test@example.com').count(), 1)

    def test_reactivate_inactive(self):
        sub = NewsletterSubscriber.objects.create(email='test@example.com', active=False)
        resp = self.client.post('/api/newsletter/subscribe/', {'email': 'test@example.com'})
        self.assertEqual(resp.status_code, 200)
        sub.refresh_from_db()
        self.assertTrue(sub.active)

    def test_unsubscribe(self):
        sub = NewsletterSubscriber.objects.create(email='test@example.com', active=True)
        resp = self.client.post('/api/newsletter/unsubscribe/', {'email': 'test@example.com'})
        self.assertEqual(resp.status_code, 200)
        sub.refresh_from_db()
        self.assertFalse(sub.active)

    def test_subscribe_missing_email(self):
        resp = self.client.post('/api/newsletter/subscribe/', {'name': 'Test'})
        self.assertEqual(resp.status_code, 400)
