"""
AI service wrapper for Vision and Text APIs (Sprint 5 — PA-13, SO-16, SO-17).
Uses OpenAI. Encrypted keys from PlatformSettings. Rate limit per store per day.
"""

import json
import time

from django.db.models import Q
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


def onboarding_suggest_theme(
    business_type: str,
    brand_name: str,
    slogan: str,
    audience: str,
    style: str,
    favorite_color: str,
    store,
    preset_slugs: list,
    block_ids: list,
) -> dict:
    """
    SO-06: Suggest theme preset + colors + home layout from onboarding answers. Consumes rate limit.
    Returns dict: theme_slug, primary_color, secondary_color, accent_color, block_order (subset of block_ids).
    """
    _check_and_consume_rate_limit(store)
    ps = PlatformSettings.load()
    client = _get_client()
    model = ps.text_model or "gpt-4o-mini"

    presets_str = ", ".join(preset_slugs) if preset_slugs else "minimal, bold-commerce, elegant, creator"
    blocks_str = ", ".join(block_ids) if block_ids else "hero, product_grid, category_grid, banner, newsletter, custom"

    prompt = f"""You are an e-commerce design advisor. Based on the following store info, suggest a theme and layout.
Respond with a JSON object only (no markdown):
- "theme_slug": MUST be exactly one of: {presets_str}
- "primary_color": hex color e.g. #6366f1 (main brand color)
- "secondary_color": hex color
- "accent_color": hex color (for CTAs/highlights)
- "block_order": array of 4-6 block IDs for the home page, in order. Each must be one of: {blocks_str}. Example: ["hero", "product_grid", "category_grid", "banner", "newsletter"]

Store info:
- Business type: {business_type or "general"}
- Brand name: {brand_name or "—"}
- Slogan: {slogan or "—"}
- Target audience: {audience or "—"}
- Preferred style: {style or "—"}
- Favorite color: {favorite_color or "—"}
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
            theme_slug = (data.get("theme_slug") or "minimal").strip().lower()
            if theme_slug not in preset_slugs:
                theme_slug = preset_slugs[0] if preset_slugs else "minimal"
            order = data.get("block_order") or block_ids[:6]
            order = [b for b in order if b in block_ids][:8]
            if not order:
                order = block_ids[:6]

            def hex_val(s):
                s = (s or "").strip()
                if s.startswith("#") and len(s) in (4, 7):
                    return s
                return "#6366f1"

            return {
                "theme_slug": theme_slug,
                "primary_color": hex_val(data.get("primary_color")),
                "secondary_color": hex_val(data.get("secondary_color")),
                "accent_color": hex_val(data.get("accent_color")),
                "block_order": order,
            }
        except json.JSONDecodeError as e:
            raise AIError(f"Invalid JSON: {e}", user_message="پیشنهاد نامعتبر. می‌توانید تم و چیدمان را دستی انتخاب کنید.")
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise AIError(str(e), user_message="خطا در تحلیل. می‌توانید از «شروع از صفر» استفاده کنید.")


def search_products_for_chat(query: str, store) -> str:
    """
    Simple keyword search on active products to build context string for RAG chat.
    Returns top 5 products as formatted text.
    """
    from catalog.models import Product

    words = [w.strip() for w in query.split() if len(w.strip()) >= 2]
    if not words:
        # Return a sample of active products
        products = Product.objects.filter(store=store, status="active").prefetch_related("variants")[:5]
    else:
        q_filter = None
        for word in words:
            condition = Q(name__icontains=word) | Q(description__icontains=word)
            q_filter = condition if q_filter is None else q_filter | condition
        products = Product.objects.filter(
            store=store, status="active"
        ).filter(q_filter).prefetch_related("variants")[:5]

    if not products:
        return "محصولی در این فروشگاه یافت نشد."

    lines = []
    for p in products:
        first_variant = p.variants.filter(is_active=True).first()
        price_str = f"{first_variant.price:,}" if first_variant else "نامشخص"
        stock_str = str(first_variant.total_stock) if first_variant else "نامشخص"
        lines.append(f"محصول: {p.name} | قیمت: {price_str} ریال | موجودی: {stock_str}")

    return "\n".join(lines)


def chat_with_products(session_messages: list, product_context: str, store) -> str:
    """
    session_messages: [{"role": "user"|"assistant", "content": "..."}]
    product_context: formatted string of relevant products
    Returns assistant reply string.
    """
    _check_and_consume_rate_limit(store)
    ps = PlatformSettings.load()
    client = _get_client()
    model = ps.text_model or "gpt-4o-mini"

    system_prompt = (
        "شما یک دستیار فروش مفید فارسی‌زبان برای یک فروشگاه اینترنتی هستید. "
        "از کاتالوگ محصولات زیر برای پاسخ به سوالات استفاده کنید. "
        "کوتاه و مفید پاسخ بدهید. همیشه به فارسی پاسخ بدهید.\n\n"
        "محصولات موجود:\n" + product_context
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(session_messages[-10:])  # last 10 messages for context

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=512,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_msg = str(e).lower()
            if "rate" in err_msg or "quota" in err_msg or "429" in err_msg:
                raise AIError(str(e), user_message="محدودیت درخواست API. بعداً تلاش کنید.")
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise AIError(str(e), user_message="خطا در دستیار هوشمند. لطفاً بعداً امتحان کنید.")


def call_vision_ai(store, image_file, prompt: str) -> str:
    """
    SO-34: Generic Vision AI call for receipt/invoice OCR.
    Accepts an uploaded image file, encodes it to base64, and calls GPT-4o vision.
    Returns the raw text response from the model.
    """
    import base64

    _check_and_consume_rate_limit(store)
    ps = PlatformSettings.load()
    client = _get_client()
    model = ps.vision_model or "gpt-4o"

    image_data = image_file.read()
    image_b64 = base64.b64encode(image_data).decode("utf-8")
    # Try to detect MIME type from file name
    name = getattr(image_file, "name", "receipt.jpg").lower()
    if name.endswith(".png"):
        mime = "image/png"
    elif name.endswith(".webp"):
        mime = "image/webp"
    elif name.endswith(".gif"):
        mime = "image/gif"
    else:
        mime = "image/jpeg"

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
                                "image_url": {"url": f"data:{mime};base64,{image_b64}"},
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
            return text
        except Exception as e:
            err_msg = str(e).lower()
            if "rate" in err_msg or "quota" in err_msg or "429" in err_msg:
                raise AIError(str(e), user_message="محدودیت درخواست API. بعداً تلاش کنید.")
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise AIError(str(e), user_message="خطا در استخراج اطلاعات فاکتور. تصویر را بررسی کنید یا اطلاعات را دستی وارد کنید.")


def call_text_ai(store, prompt: str) -> str:
    """
    SO-36: Generic text AI call. Consumes rate limit.
    Sends `prompt` to the configured text model and returns the raw string response.
    Strips markdown code blocks if present.
    """
    _check_and_consume_rate_limit(store)
    ps = PlatformSettings.load()
    client = _get_client()
    model = ps.text_model or "gpt-4o-mini"

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            return text
        except Exception as e:
            err_msg = str(e).lower()
            if "rate" in err_msg or "quota" in err_msg or "429" in err_msg:
                raise AIError(str(e), user_message="محدودیت درخواست API. بعداً تلاش کنید.")
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise AIError(str(e), user_message="خطا در تولید گزارش AI. لطفاً بعداً امتحان کنید.")


def text_generate_brand_identity(
    brand_name: str,
    business_type: str,
    style: str,
    base_color: str,
    store,
) -> dict:
    """
    SO-07: Generate tagline and brand story. Consumes rate limit.
    Returns dict: tagline, brand_story.
    """
    _check_and_consume_rate_limit(store)
    ps = PlatformSettings.load()
    client = _get_client()
    model = ps.text_model or "gpt-4o-mini"

    prompt = f"""Generate brand identity copy in Persian (فارسی). Respond with a JSON object only (no markdown):
- "tagline": short slogan for the brand, one short sentence (under 80 chars)
- "brand_story": 2-4 sentences describing the brand story and values, in Persian

Brand name: {brand_name or "—"}
Business type: {business_type or "—"}
Style: {style or "—"}
Base color preference: {base_color or "—"}
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
                "tagline": (data.get("tagline") or "")[:300],
                "brand_story": (data.get("brand_story") or "")[:2000],
            }
        except json.JSONDecodeError as e:
            raise AIError(f"Invalid JSON: {e}", user_message="خروجی نامعتبر. دوباره امتحان کنید.")
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            raise AIError(str(e), user_message="خطا در تولید هویت برند.")


def generate_logo_image(store, brand_name: str, style: str = "minimal", colors: str = "blue and white") -> str:
    """تولید لوگو با DALL-E 3 برای فروشگاه (SO-07).

    Returns:
        URL تصویر تولیدشده (رشته)
    Raises:
        AIError در صورت بروز خطا
    """
    _check_and_consume_rate_limit(store)
    client = _get_client()

    prompt = (
        f'A professional minimalist logo for a brand called "{brand_name}". '
        f"Style: {style}, clean, modern. "
        f"Colors: {colors}. "
        "No text in the logo. Simple icon suitable for e-commerce. "
        "White background, high contrast."
    )

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        raise AIError(str(e), user_message=f"خطا در تولید تصویر لوگو: {e}")
