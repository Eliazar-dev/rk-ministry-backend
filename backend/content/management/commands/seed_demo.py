from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import Album, Article, Devotional, Lesson, PastorProfile, Sermon
from shop.models import Product

YT = 'https://www.youtube.com/watch?v=aqz-KE-bpKQ'


def img(seed, w=800, h=500):
    return f'https://picsum.photos/seed/{seed}/{w}/{h}'


class Command(BaseCommand):
    help = 'Fill an empty database with starter content so the site is not blank. Safe to re-run: skips tables that already have rows.'

    def handle(self, *args, **opts):
        today = timezone.localdate()

        def fill(model, rows):
            if model.objects.exists():
                self.stdout.write(f'skip {model.__name__} (already has data)')
                return
            model.objects.bulk_create([model(**r) for r in rows])
            self.stdout.write(self.style.SUCCESS(f'added {len(rows)} {model.__name__}'))

        # Carousel videos are added automatically by the migrations (see content/migrations/0003).
        fill(Sermon, [
            {'title': t, 'category': c, 'youtube_url': YT, 'cover_url': img(f'sermon{i}'), 'date': today - timedelta(days=7 * i)}
            for i, (t, c) in enumerate([
                ('Walking in Faith When You Cannot See', 'Faith'), ('The Power of a Surrendered Life', 'Surrender'),
                ('Hope Beyond the Storm', 'Hope'), ('Prayer That Moves Mountains', 'Prayer'),
                ('Grace That Restores', 'Grace'), ('Called to Serve', 'Service')])
        ])
        fill(Lesson, [
            {'title': t, 'quarter': 'Q4 2026', 'date_range': r, 'youtube_url': YT, 'cover_url': img(f'lesson{i}'),
             'start_date': today - timedelta(days=7 * i)}
            for i, (t, r) in enumerate([
                ('Lesson 6: Faith That Works', 'Nov 1 – Nov 7'), ('Lesson 5: Living by Grace', 'Oct 25 – Oct 31'),
                ('Lesson 4: The Great Controversy', 'Oct 18 – Oct 24'), ('Lesson 3: Rest in Christ', 'Oct 11 – Oct 17')])
        ])
        fill(Devotional, [
            {'title': t, 'author': a, 'scripture': s, 'excerpt': e, 'body': e + ' ' * 1 + 'Take a moment to pray and reflect today.',
             'cover_url': img(f'dev{i}'), 'date': today - timedelta(days=i)}
            for i, (t, a, s, e) in enumerate([
                ('Morning Strength', 'Richard Kwanya Snr', 'Psalm 5:3', 'Begin each day by placing your plans in God’s hands.'),
                ('Peace in the Waiting', 'Grace Wanjiru', 'Isaiah 40:31', 'Waiting is not wasted when God is working.'),
                ('A Heart of Gratitude', 'Richard Kwanya Snr', '1 Thess 5:18', 'Gratitude turns what we have into enough.')])
        ])
        sections = {
            'blog': ['Why Every Believer Is a Missionary', 'Raising a Family Altar'],
            'literature': ['Door-to-Door Evangelism Guide', 'Training Your Team'],
            'medical': ['Eight Laws of Health', 'Community Health Outreach'],
            'children': ['David and Goliath', 'Noah and the Ark'],
            'ebook': ['Prayer Journal Template', 'Family Worship Ideas'],
        }
        fill(Article, [
            {'section': sec, 'title': t, 'excerpt': 'Replace this sample text from the admin.', 'body': 'Sample content.',
             'cover_url': img(f'{sec}{i}'), 'category': sec.title()}
            for sec, titles in sections.items() for i, t in enumerate(titles)
        ])
        fill(Album, [
            {'title': t, 'location': loc, 'cover_url': img(f'album{i}', 800, 600), 'date': today - timedelta(days=45 * i),
             'photos_url': 'https://www.pixieset.com/', 'description': 'Sample album. Replace the link and cover from the admin.'}
            for i, (t, loc) in enumerate([
                ('Eldoret Crusade', 'Eldoret'), ('Baptism Sabbath', 'Baraton'), ('Medical Camp', 'Nandi'),
                ('Children Programme', 'Kapsabet'), ('Village Outreach', 'Uasin Gishu'), ('Youth Rally', 'Eldoret')])
        ])
        fill(PastorProfile, [{'name': 'Richard Kwanya Snr', 'title': 'Evangelist', 'short_intro': 'Biography coming soon.',
                              'biography': 'Biography coming soon. Add it from the admin under Pastor profile.'}])
        fill(Product, [
            {'name': n, 'price': p, 'description': d, 'image_url': img(f'prod{i}')}
            for i, (n, p, d) in enumerate([
                ('Study Bible (NKJV)', 2500, 'Large-print study Bible with cross references.'),
                ('Sabbath School Quarterly Pack', 600, 'This quarter’s complete study guides.'),
                ('#Babawa T-Shirt', 1200, 'Premium cotton tee in navy with gold print.'),
                ('Prayer Journal', 800, 'Hardcover journal with guided prompts.')])
        ])
