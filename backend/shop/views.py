from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.auth import OptionalJWT

from . import mpesa, services
from .models import Donation, Order, OrderItem, Product
from .serializers import ProductSerializer


class ProductList(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = [OptionalJWT]
    serializer_class = ProductSerializer
    queryset = Product.objects.filter(active=True)


def _payment_json(obj):
    return {'id': obj.id, 'status': obj.status, 'amount': obj.amount, 'reason': obj.failure_reason, 'receipt': obj.mpesa_receipt}


class OrderCreate(APIView):
    def post(self, request):
        d = request.data
        name, email = (d.get('name') or '').strip(), (d.get('email') or '').strip()
        location = (d.get('location') or '').strip()
        phone = mpesa.normalize_phone(d.get('phone'))
        if not (name and email and location):
            return Response({'detail': 'Name, email and location are required.'}, status=400)
        if not phone:
            return Response({'detail': 'Enter a valid Safaricom number, e.g. 0712 345 678.'}, status=400)

        # Prices always come from the database, never from the browser.
        lines = []
        for raw in d.get('items') or []:
            product = Product.objects.filter(pk=raw.get('id'), active=True).first()
            qty = max(1, min(int(raw.get('qty') or 1), 50))
            if product:
                lines.append((product, qty))
        if not lines:
            return Response({'detail': 'Your cart is empty.'}, status=400)
        total = sum(p.price * q for p, q in lines)

        order = Order.objects.create(user=request.user, name=name, email=email, location=location, phone=phone, amount=total)
        for p, q in lines:
            OrderItem.objects.create(order=order, product=p, name=p.name, price=p.price, qty=q)

        cid, err = mpesa.stk_push(phone, total, order.ref, 'Store order')
        if err:
            services.mark_failed(order, err)
            return Response({'detail': err}, status=502)
        order.checkout_request_id = cid
        order.save(update_fields=['checkout_request_id'])
        return Response({**_payment_json(order), 'ref': order.ref, 'simulated': cid.startswith('SIM-')}, status=201)


class OrderDetail(APIView):
    def get(self, request, pk):
        order = Order.objects.filter(pk=pk, user=request.user).first()
        if not order:
            return Response(status=404)
        services.refresh_simulated(order)
        order.refresh_from_db()
        return Response({**_payment_json(order), 'ref': order.ref})


class DonationCreate(APIView):
    def post(self, request):
        try:
            amount = int(request.data.get('amount') or 0)
        except (TypeError, ValueError):
            amount = 0
        phone = mpesa.normalize_phone(request.data.get('phone'))
        if amount < 10:
            return Response({'detail': 'Minimum donation is KES 10.'}, status=400)
        if not phone:
            return Response({'detail': 'Enter a valid Safaricom number, e.g. 0712 345 678.'}, status=400)
        donation = Donation.objects.create(
            user=request.user, name=request.user.display_name, email=request.user.email, phone=phone, amount=amount
        )
        cid, err = mpesa.stk_push(phone, amount, f'DON{donation.id}', 'Donation')
        if err:
            services.mark_failed(donation, err)
            return Response({'detail': err}, status=502)
        donation.checkout_request_id = cid
        donation.save(update_fields=['checkout_request_id'])
        return Response({**_payment_json(donation), 'simulated': cid.startswith('SIM-')}, status=201)


class DonationDetail(APIView):
    def get(self, request, pk):
        donation = Donation.objects.filter(pk=pk, user=request.user).first()
        if not donation:
            return Response(status=404)
        services.refresh_simulated(donation)
        donation.refresh_from_db()
        return Response(_payment_json(donation))


class MpesaCallback(APIView):
    """Safaricom posts the payment result here (no auth — it comes from Safaricom)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        cb = (request.data.get('Body') or {}).get('stkCallback') or {}
        obj = services.find_by_checkout_id(cb.get('CheckoutRequestID', ''))
        if obj:
            if cb.get('ResultCode') == 0:
                items = {i.get('Name'): i.get('Value') for i in (cb.get('CallbackMetadata') or {}).get('Item', [])}
                services.mark_paid(obj, str(items.get('MpesaReceiptNumber', '')))
            else:
                services.mark_failed(obj, cb.get('ResultDesc', 'Payment was not completed.'))
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'})
