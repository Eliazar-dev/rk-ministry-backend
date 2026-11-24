"""Safaricom Daraja STK push. If credentials are missing, the app runs in simulate mode."""
import base64
import re
import uuid
from datetime import datetime

import requests
from django.conf import settings


def configured():
    s = settings
    base_ok = all([s.MPESA_CONSUMER_KEY, s.MPESA_CONSUMER_SECRET, s.MPESA_PASSKEY, s.MPESA_CALLBACK_URL])
    # For Buy Goods/Till, also require the till number
    if getattr(s, 'MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline') == 'CustomerBuyGoodsOnline':
        return base_ok and bool(getattr(s, 'MPESA_TILL_NUMBER', ''))
    return base_ok


def normalize_phone(raw):
    """07xx / 01xx / +2547xx / 2547xx  ->  2547xxxxxxxx. Returns None if invalid."""
    digits = re.sub(r'\D', '', raw or '')
    if digits.startswith('254') and len(digits) == 12:
        pass
    elif digits.startswith('0') and len(digits) == 10:
        digits = '254' + digits[1:]
    elif len(digits) == 9 and digits[0] in '71':
        digits = '254' + digits
    else:
        return None
    return digits if digits[3] in '71' else None


def _base():
    return 'https://api.safaricom.co.ke' if settings.MPESA_ENV == 'production' else 'https://sandbox.safaricom.co.ke'


def _token():
    r = requests.get(
        f'{_base()}/oauth/v1/generate?grant_type=client_credentials',
        auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
        timeout=8,  # Vercel functions are short-lived; fail fast
    )
    r.raise_for_status()
    return r.json()['access_token']


def _stk_request(phone, amount, reference, description, transaction_type):
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{ts}'.encode()).decode()

    # For Buy Goods/Till, PartyB is the actual Till number (different from BusinessShortCode)
    party_b = settings.MPESA_TILL_NUMBER if transaction_type == 'CustomerBuyGoodsOnline' and settings.MPESA_TILL_NUMBER else settings.MPESA_SHORTCODE

    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': ts,
        'TransactionType': transaction_type,
        'Amount': int(amount),
        'PartyA': phone,
        'PartyB': party_b,
        'PhoneNumber': phone,
        'CallBackURL': settings.MPESA_CALLBACK_URL,
        'AccountReference': reference[:12],
        'TransactionDesc': description[:13],
    }
    r = requests.post(
        f'{_base()}/mpesa/stkpush/v1/processrequest',
        json=payload,
        headers={'Authorization': f'Bearer {_token()}'},
        timeout=8,
    )
    data = r.json()
    if data.get('ResponseCode') == '0':
        return data['CheckoutRequestID'], None
    return '', data.get('errorMessage') or data.get('ResponseDescription') or 'M-Pesa request failed.'


def stk_push(phone, amount, reference, description):
    """Returns (checkout_request_id, error). In simulate mode the id starts with SIM-."""
    if not configured():
        return 'SIM-' + uuid.uuid4().hex[:12], None
    try:
        primary = getattr(settings, 'MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline')
        alternate = 'CustomerBuyGoodsOnline' if primary == 'CustomerPayBillOnline' else 'CustomerPayBillOnline'
        cid, err = _stk_request(phone, amount, reference, description, primary)
        if cid:
            return cid, None
        # Daraja rejects a mismatched shortcode type with "unresolved reason type" —
        # a rejected push never reaches the phone, so retrying with the other type is safe.
        if 'unresolved reason' in (err or '').lower() or 'invalid transaction' in (err or '').lower():
            # For Buy Goods fallback, ensure till number is set
            if alternate == 'CustomerBuyGoodsOnline' and not getattr(settings, 'MPESA_TILL_NUMBER', ''):
                return '', 'Till number not configured for Buy Goods transaction'
            cid, err = _stk_request(phone, amount, reference, description, alternate)
            if cid:
                return cid, None
        return '', err
    except Exception as exc:  # network / auth problems
        return '', f'Could not reach M-Pesa: {exc}'
