from django.test import TestCase
from rest_framework.test import APIClient
from content.models import Lesson, LessonPage
from accounts.models import User


class LessonPagesStaffTests(TestCase):
    """Test lesson pages CRUD and reorder in staff panel."""

    def setUp(self):
        # Clean up any existing data before each test
        LessonPage.objects.all().delete()
        Lesson.objects.all().delete()
        
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            first_name='Staff User',
            password='testpass123',
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            email='regular@example.com',
            first_name='Regular User',
            password='testpass123',
            is_staff=False,
        )
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            quarter='Q4 2026',
            date_range='Nov 1 – Nov 7',
            teacher='Richard Kwanya Snr',
            youtube_url='https://youtube.com/watch?v=test',
            published=True,
        )

    def test_non_staff_gets_401(self):
        """Non-staff user should get 401 on lesson pages endpoint."""
        response = self.client.get('/api/manage/lesson-pages/')
        self.assertEqual(response.status_code, 401)

    def test_non_staff_authenticated_gets_403(self):
        """Authenticated non-staff user should get 403."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/manage/lesson-pages/')
        self.assertEqual(response.status_code, 403)

    def test_staff_can_list_pages(self):
        """Staff user can list lesson pages."""
        self.client.force_authenticate(user=self.staff_user)
        LessonPage.objects.all().delete()  # Clean up any existing pages
        page = LessonPage.objects.create(
            lesson=self.lesson,
            image_url='https://example.com/page1.jpg',
            label='Page 1',
            order=0,
        )
        response = self.client.get('/api/manage/lesson-pages/')
        self.assertEqual(response.status_code, 200)
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        page_ids = [p['id'] for p in results]
        self.assertIn(page.id, page_ids)

    def test_staff_can_create_page(self):
        """Staff user can create a lesson page."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            '/api/manage/lesson-pages/',
            {
                'lesson': self.lesson.id,
                'image_url': 'https://example.com/newpage.jpg',
                'label': 'New Page',
                'order': 0,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LessonPage.objects.count(), 1)

    def test_staff_can_update_page(self):
        """Staff user can update a lesson page."""
        self.client.force_authenticate(user=self.staff_user)
        page = LessonPage.objects.create(
            lesson=self.lesson,
            image_url='https://example.com/page1.jpg',
            label='Page 1',
            order=0,
        )
        response = self.client.patch(
            f'/api/manage/lesson-pages/{page.id}/',
            {'label': 'Updated Label'},
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.label, 'Updated Label')

    def test_staff_can_delete_page(self):
        """Staff user can delete a lesson page."""
        self.client.force_authenticate(user=self.staff_user)
        page = LessonPage.objects.create(
            lesson=self.lesson,
            image_url='https://example.com/page1.jpg',
            label='Page 1',
            order=0,
        )
        response = self.client.delete(f'/api/manage/lesson-pages/{page.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(LessonPage.objects.count(), 0)

    def test_staff_can_reorder_pages(self):
        """Staff user can reorder lesson pages."""
        self.client.force_authenticate(user=self.staff_user)
        page1 = LessonPage.objects.create(
            lesson=self.lesson,
            image_url='https://example.com/page1.jpg',
            label='Page 1',
            order=0,
        )
        page2 = LessonPage.objects.create(
            lesson=self.lesson,
            image_url='https://example.com/page2.jpg',
            label='Page 2',
            order=1,
        )
        response = self.client.post(
            '/api/manage/lesson-pages/reorder/',
            [
                {'id': page1.id, 'order': 1},
                {'id': page2.id, 'order': 0},
            ],
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        page1.refresh_from_db()
        page2.refresh_from_db()
        self.assertEqual(page1.order, 1)
        self.assertEqual(page2.order, 0)

    def test_can_filter_pages_by_lesson(self):
        """Lesson pages can be filtered by lesson ID."""
        self.client.force_authenticate(user=self.staff_user)
        LessonPage.objects.all().delete()  # Clean up
        lesson2 = Lesson.objects.create(
            title='Test Lesson 2',
            quarter='Q4 2026',
            date_range='Nov 8 – Nov 14',
            teacher='Richard Kwanya Snr',
            youtube_url='https://youtube.com/watch?v=test2',
            published=True,
        )
        page1 = LessonPage.objects.create(
            lesson=self.lesson,
            image_url='https://example.com/page1.jpg',
            label='Page 1',
            order=0,
        )
        LessonPage.objects.create(
            lesson=lesson2,
            image_url='https://example.com/page2.jpg',
            label='Page 2',
            order=0,
        )
        response = self.client.get(f'/api/manage/lesson-pages/?lesson={self.lesson.id}')
        self.assertEqual(response.status_code, 200)
        results = response.data['results'] if isinstance(response.data, dict) else response.data
        page_ids = [p['id'] for p in results]
        self.assertIn(page1.id, page_ids)
        # Pages from the other lesson must not appear
        other_ids = set(LessonPage.objects.exclude(lesson=self.lesson).values_list('id', flat=True))
        self.assertFalse(set(page_ids) & other_ids)
