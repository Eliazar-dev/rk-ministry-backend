from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Donation, Order, Payment

SIMULATE_AFTER = timedelta(seconds=25)


def _order_email(order):
    lines = '\n'.join(f'  • {i.name} × {i.qty} — KES {i.price * i.qty:,}' for i in order.items.all())
    body = (
        f'Dear {order.name},\n\n'
        f'Thank you for your order with {settings.SITE_NAME}. Your payment was received.\n\n'
        f'Order reference: {order.ref}\n'
        f'M-Pesa receipt: {order.mpesa_receipt or "—"}\n'
        f'Delivery location: {order.location}\n\n'
        f'{lines}\n\nTotal: KES {order.amount:,}\n\n'
        'God bless you.\nRichard Kwanya Snr #Babawa\n'
    )
    send_mail(f'Order {order.ref} confirmed', body, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=True)


def _donation_email(d):
    if not d.email:
        return
    body = (
        f'Dear {d.name},\n\nThank you for your generous gift of KES {d.amount:,} to {settings.SITE_NAME}. '
        f'M-Pesa receipt: {d.mpesa_receipt or "—"}.\n\nYour giving helps us equip people and transform lives.\n\n'
        'God bless you.\nRichard Kwanya Snr #Babawa\n'
    )
    send_mail('Thank you for your donation', body, settings.DEFAULT_FROM_EMAIL, [d.email], fail_silently=True)


def mark_paid(obj, receipt=''):
    if obj.status == Payment.PAID:
        return
    obj.status = Payment.PAID
    obj.mpesa_receipt = receipt or obj.mpesa_receipt
    obj.save()
    if not obj.receipt_sent:
        _order_email(obj) if isinstance(obj, Order) else _donation_email(obj)
        obj.receipt_sent = True
        obj.save(update_fields=['receipt_sent'])


def mark_failed(obj, reason=''):
    if obj.status == Payment.PENDING:
        obj.status = Payment.FAILED
        obj.failure_reason = reason[:200]
        obj.save(update_fields=['status', 'failure_reason'])


def refresh_simulated(obj):
    """Simulate mode (no Daraja keys): auto-confirm shortly after the prompt was 'sent'."""
    if obj.status == Payment.PENDING and obj.checkout_request_id.startswith('SIM-'):
        if timezone.now() - obj.created >= SIMULATE_AFTER:
            mark_paid(obj, 'SIMULATED')


def find_by_checkout_id(cid):
    return Order.objects.filter(checkout_request_id=cid).first() or Donation.objects.filter(checkout_request_id=cid).first()
