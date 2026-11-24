from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from content.models import Sermon, Lesson, Article


@receiver(post_save, sender=Sermon)
@receiver(post_save, sender=Lesson)
@receiver(post_save, sender=Article)
def notify_new_content(sender, instance, created, **kwargs):
    if not created:
        return

    # Run in on_commit to avoid blocking the save
    transaction.on_commit(lambda: send_notification_email(sender, instance))


def send_notification_email(sender, instance):
    from .models import NewsletterSubscriber

    content_type = {
        'Sermon': 'Sermon',
        'Lesson': 'Sabbath School Lesson',
        'Article': 'Article',
    }.get(sender.__name__, 'Content')

    title = getattr(instance, 'title', '')
    section = getattr(instance, 'section', '')

    subject = f'New {content_type}: {title}'
    message = f"A new {content_type.lower()} has been published:\n\n" \
              f"Title: {title}\n" \
              f"{f'Section: {section}\n' if section else ''}" \
              f"\nVisit {settings.FRONTEND_URL} to view it.\n\n" \
              f"To unsubscribe, visit {settings.FRONTEND_URL}/newsletter/unsubscribe"

    recipients = list(NewsletterSubscriber.objects.filter(active=True).values_list('email', flat=True))

    if recipients:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@richardkwanya.org'),
                recipient_list=recipients,
                fail_silently=True,
            )
        except Exception:
            pass
