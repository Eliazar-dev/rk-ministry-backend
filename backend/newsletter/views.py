from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import NewsletterSubscriber
from .serializers import NewsletterSubscriberSerializer


class NewsletterSubscribe(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        name = (request.data.get('name') or '').strip()

        if not email:
            return Response({'detail': 'Email is required.'}, status=400)

        sub, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={'name': name, 'active': True}
        )

        if not sub.active:
            sub.active = True
            sub.unsubscribed_at = None
            sub.save()

        if created or not sub.active:
            self.send_welcome_email(sub)

        serializer = NewsletterSubscriberSerializer(sub)
        return Response(serializer.data, status=201 if created else 200)

    def send_welcome_email(self, subscriber):
        try:
            send_mail(
                subject='Welcome to Richard Kwanya Snr Ministry',
                message=f"Thank you for subscribing, {subscriber.name or subscriber.email}!\n\n"
                        f"You'll receive updates when new sermons, lessons, devotionals, or other content is published.\n\n"
                        f"To unsubscribe, visit {settings.FRONTEND_URL}/newsletter/unsubscribe",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@richardkwanya.org'),
                recipient_list=[subscriber.email],
                fail_silently=True,
            )
        except Exception:
            pass


class NewsletterUnsubscribe(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'detail': 'Email is required.'}, status=400)

        sub = NewsletterSubscriber.objects.filter(email=email).first()
        if sub:
            sub.active = False
            sub.unsubscribed_at = None
            sub.save()
        return Response({'detail': 'Unsubscribed successfully.'}, status=200)


class NewsletterList(APIView):
    def get(self, request):
        if not request.user or not request.user.is_staff:
            return Response(status=403)
        subs = NewsletterSubscriber.objects.filter(active=True)
        serializer = NewsletterSubscriberSerializer(subs, many=True)
        return Response(serializer.data)


class NewsletterMe(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = NewsletterSubscriber.objects.filter(email=request.user.email).first()
        if sub:
            return Response({'subscribed': sub.active, 'name': sub.name})
        return Response({'subscribed': False, 'name': None})
