from django.contrib import admin
from django.utils.html import format_html

from .models import Donation, Order, OrderItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'name', 'price', 'active')
    list_editable = ('price', 'active')
    search_fields = ('name',)
    fields = ('name', 'price', 'image', 'image_url', 'description', 'active')

    def thumb(self, obj):
        return format_html('<img src="{}" style="height:44px;border-radius:6px"/>', obj.image_src) if obj.image_src else '—'


class ItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'name', 'price', 'qty')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('ref', 'name', 'phone', 'location', 'amount', 'status', 'mpesa_receipt', 'created')
    list_filter = ('status', 'created')
    search_fields = ('ref', 'name', 'email', 'phone', 'mpesa_receipt')
    readonly_fields = ('ref', 'checkout_request_id', 'mpesa_receipt', 'receipt_sent', 'created')
    inlines = [ItemInline]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'amount', 'status', 'mpesa_receipt', 'created')
    list_filter = ('status', 'created')
    search_fields = ('name', 'email', 'phone', 'mpesa_receipt')
    readonly_fields = ('checkout_request_id', 'mpesa_receipt', 'receipt_sent', 'created')
