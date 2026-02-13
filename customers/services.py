"""
OTP service: create/send and verify login OTP. SMS is abstracted (mock in v1).
"""
import random
import string
from datetime import timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction

from .models import Customer, LoginOTP, normalize_phone

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_VERIFY_ATTEMPTS = 5
RATE_LIMIT_KEY_PREFIX = "otp_request:"
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 3


def _rate_limit_key(store_id, phone, ip):
    return f"{RATE_LIMIT_KEY_PREFIX}{store_id}:{phone}:{ip}"


def _check_rate_limit(store_id, phone, ip):
    key = _rate_limit_key(store_id, phone, ip)
    count = cache.get(key, 0)
    if count >= RATE_LIMIT_MAX_REQUESTS:
        return False
    return True


def _increment_rate_limit(store_id, phone, ip):
    key = _rate_limit_key(store_id, phone, ip)
    count = cache.get(key, 0) + 1
    cache.set(key, count, timeout=RATE_LIMIT_WINDOW_SECONDS)
    return count


def _send_sms_mock(phone, code):
    """Mock SMS sender. Replace with real provider (e.g. Kavenegar) later."""
    # In development, log to console
    import logging
    logging.getLogger(__name__).info(f"[OTP mock] phone={phone} code={code}")
    return True


def create_and_send_login_otp(store, phone, request=None):
    """
    Create a login OTP, store it, send via SMS (or mock). Returns (success, message).
    Respects rate limit by store+phone+IP.
    """
    phone = normalize_phone(phone)
    if not phone or len(phone) < 10:
        return False, "شماره موبایل معتبر نیست."

    store_id = store.pk if store else 0
    ip = request.META.get("REMOTE_ADDR", "") if request else ""
    if not _check_rate_limit(store_id, phone, ip):
        return False, "تعداد درخواست‌ها بیش از حد است. چند دقیقه دیگر تلاش کنید."

    code = "".join(random.choices(string.digits, k=OTP_LENGTH))
    expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    with transaction.atomic():
        # Invalidate any previous unused OTPs for this phone in this store
        LoginOTP.objects.filter(
            store=store,
            phone=phone,
            purpose=LoginOTP.PURPOSE_LOGIN,
            is_used=False,
        ).update(is_used=True)
        LoginOTP.objects.create(
            store=store,
            phone=phone,
            code=code,
            purpose=LoginOTP.PURPOSE_LOGIN,
            expires_at=expires_at,
        )

    _increment_rate_limit(store_id, phone, ip)
    _send_sms_mock(phone, code)
    return True, "کد ورود ارسال شد."


def verify_login_otp(store, phone, code):
    """
    Verify OTP; if valid, get or create Customer for (store, phone) and return it.
    Returns (customer, error_message). customer is None on failure.
    """
    phone = normalize_phone(phone)
    if not phone or not code:
        return None, "شماره موبایل و کد را وارد کنید."

    otp = (
        LoginOTP.objects.filter(
            store=store,
            phone=phone,
            purpose=LoginOTP.PURPOSE_LOGIN,
            is_used=False,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )

    if not otp:
        return None, "کد منقضی شده یا وجود ندارد. درخواست کد جدید دهید."

    otp.attempts += 1
    otp.save(update_fields=["attempts"])

    if otp.attempts > MAX_VERIFY_ATTEMPTS:
        otp.is_used = True
        otp.save(update_fields=["is_used"])
        return None, "تعداد تلاش‌ها بیش از حد. درخواست کد جدید دهید."

    if otp.code != code.strip():
        return None, "کد اشتباه است."

    otp.is_used = True
    otp.save(update_fields=["is_used"])

    with transaction.atomic():
        customer, _ = Customer.objects.get_or_create(
            store=store,
            phone=phone,
            defaults={"name": ""},
        )
        customer.last_login_at = timezone.now()
        customer.save(update_fields=["last_login_at"])

    return customer, None
