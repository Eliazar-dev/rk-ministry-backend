from django.test import TestCase
from rest_framework.test import APIClient
from content.models import Lesson
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
        """Anonymous request should have locked=True and no pdf field."""
        response = self.client.get('/api/lessons/')
        self.assertEqual(response.status_code, 200)
        data = response.data[0]
        self.assertTrue(data['locked'])
        self.assertNotIn('pdf', data)
        self.assertFalse(data['hasPdf'])  # hasPdf is false for anonymous users

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
