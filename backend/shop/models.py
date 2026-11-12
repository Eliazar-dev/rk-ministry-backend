import uuid

from cloudinary.models import CloudinaryField
from django.conf import settings
from django.db import models
from django.utils import timezone

from content.models import media_url


class Product(models.Model):
    name = models.CharField(max_length=160)
    price = models.PositiveIntegerField(help_text='Price in KES')
    image = CloudinaryField('cover image (upload)', folder='rk/products', blank=True, null=True)
    image_url = models.URLField('cover image URL', blank=True, help_text='Optional: paste a Cloudinary image URL instead of uploading.')
    description = models.TextField()
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    @property
    def image_src(self):
        return media_url(self.image) or self.image_url

    def __str__(self):
        return self.name


class Payment(models.Model):
    PENDING, PAID, FAILED = 'pending', 'paid', 'failed'
    STATUS = [(PENDING, 'Pending'), (PAID, 'Paid'), (FAILED, 'Failed')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS, default=PENDING)
    checkout_request_id = models.CharField(max_length=80, blank=True, db_index=True)
    mpesa_receipt = models.CharField(max_length=40, blank=True)
    failure_reason = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-created']


class Order(Payment):
    ref = models.CharField(max_length=12, unique=True, editable=False)
    name = models.CharField(max_length=120)
    email = models.EmailField()
    location = models.CharField(max_length=200)
    receipt_sent = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.ref:
            self.ref = 'RK' + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.ref} — {self.name} (KES {self.amount})'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=160)
    price = models.PositiveIntegerField()
    qty = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.name} × {self.qty}'


class Donation(Payment):
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    receipt_sent = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} — KES {self.amount} ({self.status})'
