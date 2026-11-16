from django.test import TestCase
from rest_framework.test import APIClient
from content.models import Lesson, LessonPage
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
