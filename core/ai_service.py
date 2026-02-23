"""
AI service wrapper for Vision and Text APIs (Sprint 5 — PA-13, SO-16, SO-17).
Uses OpenAI. Encrypted keys from PlatformSettings. Rate limit per store per day.
"""

import json
import time

from django.utils import timezone

from core.encryption import decrypt_value
from core.models import AIDailyUsage, PlatformSettings


class AIError(Exception):
    """Raised when AI call fails (config, rate limit, API error)."""
    def __init__(self, message, user_message=None):
        self.message = message
        self.user_message = user_message or "خطا در سرویس هوش مصنوعی. لطفاً تنظیمات را بررسی کنید."


def _get_client():
    """Return OpenAI client if key is configured."""
    ps = PlatformSettings.load()
    key = decrypt_value(ps.openai_api_key_encrypted) if ps.openai_api_key_encrypted else ""
    if not key:
        raise AIError("OpenAI API key not set", user_message="کلید API تنظیم نشده. در پنل ادمین تنظیمات AI را پر کنید.")
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except ImportError:
        raise AIError("openai package not installed", user_message="پکیج openai نصب نیست.")


def _check_and_consume_rate_limit(store):
    """Increment store's daily usage; raise AIError if over limit."""
    ps = PlatformSettings.load()
    if not ps.ai_enabled:
        raise AIError("AI disabled", user_message="سرویس هوش مصنوعی غیرفعال است.")
    today = timezone.now().date()
    usage, _ = AIDailyUsage.objects.get_or_create(store=store, date=today, defaults={"usage_count": 0})
    if usage.usage_count >= ps.rate_limit_per_store_daily:
        raise AIError(
            f"Rate limit exceeded ({usage.usage_count}/{ps.rate_limit_per_store_daily})",
            user_message=f"اعتبار روزانه AI به پایان رسیده ({ps.rate_limit_per_store_daily} درخواست در روز). فردا دوباره امتحان کنید.",
        )
    usage.usage_count += 1
    usage.save(update_fields=["usage_count"])


def get_ai_usage_today(store):
    """Return (used, limit) for today."""
    ps = PlatformSettings.load()
    today = timezone.now().date()
    usage = AIDailyUsage.objects.filter(store=store, date=today).first()
    used = usage.usage_count if usage else 0
    return used, ps.rate_limit_per_store_daily


def is_ai_available_for_store(store):
    """True if AI is enabled, key set, and under rate limit."""
    ps = PlatformSettings.load()
    if not ps.ai_enabled or not ps.openai_api_key_encrypted:
        return False
    used, limit = get_ai_usage_today(store)
    return used < limit


def vision_extract_product(image_base64: str, store) -> dict:
    """
    Call Vision API to extract product fields from image. Consumes rate limit.
    Returns dict: name, description, category_suggestion, attributes (e.g. color, size).
    """
    _check_and_consume_rate_limit(store)
    ps = PlatformSettings.load()
    client = _get_client()
    model = ps.vision_model or "gpt-4o"

    prompt = """Analyze this product image and extract structured data for an e-commerce listing.
Respond with a JSON object only (no markdown), with these keys:
- "name": product title in Persian (فارسی), short and clear
- "description": product description in Persian, 2-4 sentences
- "category_suggestion": single category name in Persian that best fits the product (e.g. "لوازم الکترونیکی", "لباس مردانه")
- "attributes": object with optional keys: "color", "size", "material" (values in Persian if applicable)

If the image is not a product or is unclear, set "name" to "تصویر نامشخص" and "description" to "لطفاً اطلاعات را دستی وارد کنید."
"""

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                            },
                        ],
                    }
                ],
                max_tokens=1024,
            )
            text = response.choices[0].message.content.strip()
            # Strip markdown code block if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            data = json.loads(text)
            return {
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "category_suggestion": data.get("category_suggestion", ""),
                "attributes": data.get("attributes") or {},
            }
        except json.JSONDecodeError as e:
            raise AIError(f"Invalid JSON from vision: {e}", user_message="خروجی نامعتبر از AI. لطفاً محصول را دستی ایجاد کنید.")
        except Exception as e:
            err_msg = str(e).lower()
            if "rate" in err_msg or "quota" in err_msg or "429" in err_msg:
                raise AIError(str(e), user_message="محدودیت درخواست API. بعداً تلاش کنید.")
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise AIError(str(e), user_message="خطا در ارتباط با سرویس Vision. لطفاً تصویر را بررسی کنید یا بعداً امتحان کنید.")


def text_generate_seo(name: str, description: str, category_names: list, lang: str, store) -> dict:
    """
    Call Text API to generate SEO fields. Consumes rate limit.
    Returns dict: meta_title, meta_description, focus_keywords, og_description.
    """
    _check_and_consume_rate_limit(store)
    ps = PlatformSettings.load()
    client = _get_client()
    model = ps.text_model or "gpt-4o-mini"

    categories_str = "، ".join(category_names) if category_names else "—"
    prompt = f"""Generate SEO metadata for this product. Language: {lang}. Respond with a JSON object only (no markdown):
- "meta_title": short SEO title (under 60 chars) in the product language
- "meta_description": meta description (under 160 chars) in the product language
- "focus_keywords": comma-separated 3-5 keywords in the product language
- "og_description": 1-2 sentence description for social sharing in the product language

Product name: {name}
Product description: {description[:500]}
Categories: {categories_str}
"""

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
            )
            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            data = json.loads(text)
            return {
                "meta_title": (data.get("meta_title") or "")[:200],
                "meta_description": (data.get("meta_description") or "")[:500],
                "focus_keywords": (data.get("focus_keywords") or "")[:500],
                "og_description": (data.get("og_description") or "")[:1000],
            }
        except json.JSONDecodeError as e:
            raise AIError(f"Invalid JSON from text: {e}", user_message="خروجی SEO نامعتبر. فیلدها را دستی پر کنید.")
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise AIError(str(e), user_message="خطا در تولید SEO. فیلدها را دستی پر کنید.")
