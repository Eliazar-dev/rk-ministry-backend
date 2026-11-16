from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from content.models import Lesson, LessonPage, LiveStream
from accounts.models import User


class LessonPDFTests(TestCase):
    """Test that PDFs are locked for visitors and available to members."""

    def setUp(self):
        self.client = APIClient()
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            quarter='Q4 2026',
            date_range='Nov 1 – Nov 7',
            teacher='Richard Kwanya Snr',
            youtube_url='https://youtube.com/watch?v=test',
            pdf_url='https://example.com/lesson.pdf',
            published=True,
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test User',
            password='testpass123',
        )

    def test_anonymous_gets_locked_no_pdf(self):
        """Anonymous request should have locked=True, no pdf field, but hasPdf stays visible."""
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        data = response.data[0]
        self.assertTrue(data['locked'])
        self.assertNotIn('pdf', data)
        self.assertTrue(data['hasPdf'])  # flag stays visible so the card can show the button

    def test_bad_token_counts_as_visitor(self):
        """An expired/invalid token must not break the public endpoint."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        data = response.data[0]
        self.assertTrue(data['locked'])
        self.assertNotIn('pdf', data)

    def test_member_gets_pdf_url(self):
        """Logged-in member should get the pdf URL and hasPdf=True."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        data = response.data[0]
        self.assertFalse(data['locked'])
        self.assertIn('pdf', data)
        self.assertEqual(data['pdf'], 'https://example.com/lesson.pdf')
        self.assertTrue(data['hasPdf'])


class LessonPagesTests(TestCase):
    """Test that lesson pages are locked for visitors and available to members."""

    def setUp(self):
        self.client = APIClient()
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            quarter='Q4 2026',
            date_range='Nov 1 – Nov 7',
            teacher='Richard Kwanya Snr',
            youtube_url='https://youtube.com/watch?v=test',
            pdf_url='https://example.com/lesson.pdf',
            published=True,
        )
        self.page1 = LessonPage.objects.create(
            lesson=self.lesson,
            image_url='https://example.com/page1.jpg',
            label='Friday, Oct 23',
            order=0,
        )
        self.page2 = LessonPage.objects.create(
            lesson=self.lesson,
            image_url='https://example.com/page2.jpg',
            label='Saturday, Oct 24',
            order=1,
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test User',
            password='testpass123',
        )

    def test_anonymous_gets_locked_no_pages(self):
        """Anonymous request should have locked=True, no pages/youtube, but flags stay visible."""
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        data = response.data[0]
        self.assertTrue(data['locked'])
        self.assertNotIn('pages', data)
        self.assertNotIn('youtube', data)
        self.assertTrue(data['hasPages'])  # flags stay visible so the card can show the buttons
        self.assertTrue(data['hasVideo'])

    def test_member_gets_pages_and_video(self):
        """Logged-in member should get pages, youtube, and flags."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        data = response.data[0]
        self.assertFalse(data['locked'])
        self.assertIn('pages', data)
        self.assertEqual(len(data['pages']), 2)
        self.assertIn('youtube', data)
        self.assertTrue(data['hasPages'])
        self.assertTrue(data['hasVideo'])

    def test_pages_are_ordered(self):
        """Pages should be returned in order."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        data = response.data[0]
        self.assertEqual(data['pages'][0]['label'], 'Friday, Oct 23')
        self.assertEqual(data['pages'][1]['label'], 'Saturday, Oct 24')


class LiveStreamTests(TestCase):
    """GET /api/live/ returns the live or next scheduled stream; YouTube link is member-only."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test User',
            password='testpass123',
        )
        self.future = timezone.now() + timezone.timedelta(hours=2)
        self.past = timezone.now() - timezone.timedelta(hours=1)

    def make(self, **kw):
        args = dict(
            title='Sabbath Service',
            youtube_url='https://youtube.com/watch?v=abc12345678',
            scheduled_at=self.future,
        )
        args.update(kw)
        return LiveStream.objects.create(**args)

    def test_empty_returns_null(self):
        response = self.client.get('/api/live/')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data)

    def test_anonymous_gets_locked_no_youtube(self):
        self.make(is_live=True)
        response = self.client.get('/api/live/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertTrue(data['locked'])
        self.assertNotIn('youtube', data)
        self.assertTrue(data['isLive'])
        self.assertEqual(data['status'], 'live')
        self.assertEqual(data['title'], 'Sabbath Service')

    def test_bad_token_counts_as_visitor(self):
        self.make(is_live=True)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')
        response = self.client.get('/api/live/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['locked'])
        self.assertNotIn('youtube', response.data)

    def test_member_gets_youtube(self):
        self.make(is_live=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/live/')
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertFalse(data['locked'])
        self.assertEqual(data['youtube'], 'https://youtube.com/watch?v=abc12345678')

    def test_live_wins_over_scheduled(self):
        self.make(title='Scheduled later', scheduled_at=self.future)
        self.make(title='On air now', is_live=True, scheduled_at=self.past)
        response = self.client.get('/api/live/')
        self.assertEqual(response.data['title'], 'On air now')

    def test_next_scheduled_returned_when_nothing_live(self):
        soon = self.make(title='Soon', scheduled_at=self.future)
        self.make(title='Later', scheduled_at=self.future + timezone.timedelta(hours=5))
        self.make(title='Past missed', scheduled_at=self.past)
        response = self.client.get('/api/live/')
        self.assertEqual(response.data['id'], soon.id)
        self.assertEqual(response.data['status'], 'scheduled')

    def test_ended_live_stream_is_not_returned(self):
        self.make(is_live=True, ends_at=self.past)
        response = self.client.get('/api/live/')
        self.assertIsNone(response.data)
