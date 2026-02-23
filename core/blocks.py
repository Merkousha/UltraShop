"""
SO-46: Block registry for drag & drop page editor (WordPress-style extensible blocks).
Each block has: id, label (Persian), template path, default_settings.
Other apps can register new blocks via register_block() in AppConfig.ready().
"""

# Built-in blocks (core). Extended by register_block() from other apps.
_BUILTIN_BLOCKS = [
    {
        "id": "hero",
        "label": "بخش برجسته (Hero)",
        "template": "storefront/blocks/hero.html",
        "default_settings": {"title": "به فروشگاه ما خوش آمدید", "subtitle": "", "cta_text": "مشاهده محصولات", "cta_url": "", "image": ""},
    },
    {
        "id": "product_grid",
        "label": "گرید محصولات",
        "template": "storefront/blocks/product_grid.html",
        "default_settings": {"columns": 4, "limit": 8, "title": "محصولات"},
    },
    {
        "id": "category_grid",
        "label": "گرید دسته‌بندی",
        "template": "storefront/blocks/category_grid.html",
        "default_settings": {"title": "دسته‌بندی‌ها"},
    },
    {
        "id": "banner",
        "label": "بنر",
        "template": "storefront/blocks/banner.html",
        "default_settings": {"image": "", "link": "", "alt": ""},
    },
    {
        "id": "testimonials",
        "label": "نقل‌قول‌های مشتریان",
        "template": "storefront/blocks/testimonials.html",
        "default_settings": {"title": "نظرات مشتریان", "items": []},
        "items_schema": [
            {"key": "author", "label": "نام"},
            {"key": "text", "label": "متن"},
        ],
    },
    {
        "id": "faq",
        "label": "سؤالات متداول",
        "template": "storefront/blocks/faq.html",
        "default_settings": {"title": "سوالات متداول", "items": []},
        "items_schema": [
            {"key": "question", "label": "سؤال"},
            {"key": "answer", "label": "پاسخ"},
        ],
    },
    {
        "id": "newsletter",
        "label": "عضویت خبرنامه",
        "template": "storefront/blocks/newsletter.html",
        "default_settings": {"title": "در خبرنامه ما عضو شوید", "button_text": "عضویت"},
    },
    {
        "id": "custom",
        "label": "بخش سفارشی (HTML)",
        "template": "storefront/blocks/custom.html",
        "default_settings": {"html": "", "title": ""},
    },
]

# Mutable registry: built-in + any blocks registered via register_block()
BLOCK_REGISTRY = list(_BUILTIN_BLOCKS)


def register_block(block_spec):
    """
    Register a new block type (WordPress-style). Call from AppConfig.ready() or at import time.
    block_spec: dict with id (str), label (str), template (path), default_settings (dict).
    If a block with the same id exists, it is replaced (allows overriding built-in).
    """
    bid = block_spec.get("id")
    if not bid:
        return
    for i, b in enumerate(BLOCK_REGISTRY):
        if b["id"] == bid:
            BLOCK_REGISTRY[i] = {
                "id": bid,
                "label": block_spec.get("label", bid),
                "template": block_spec.get("template", ""),
                "default_settings": block_spec.get("default_settings") or {},
            }
            return
    BLOCK_REGISTRY.append({
        "id": bid,
        "label": block_spec.get("label", bid),
        "template": block_spec.get("template", ""),
        "default_settings": block_spec.get("default_settings") or {},
    })


def get_block_type_id(block_id):
    """
    Resolve instance id to block type. E.g. 'banner_2' -> 'banner', 'hero' -> 'hero'.
    Allows multiple instances of the same block (e.g. multiple banners).
    """
    import re
    match = re.match(r"^(.+)_(\d+)$", block_id)
    if match:
        base, num = match.group(1), match.group(2)
        if base and num != "0" and any(b["id"] == base for b in BLOCK_REGISTRY):
            return base
    return block_id


def get_block_by_id(block_id):
    type_id = get_block_type_id(block_id)
    for b in BLOCK_REGISTRY:
        if b["id"] == type_id:
            return b
    return None


def get_instance_number(block_id):
    """For display: banner_2 -> 2, banner -> 1."""
    import re
    match = re.match(r"^(.+)_(\d+)$", block_id)
    if match:
        base, num = match.group(1), match.group(2)
        if base and any(b["id"] == base for b in BLOCK_REGISTRY):
            return int(num)
    return 1


def next_instance_id(block_type_id, current_order):
    """Return next free instance id for this type. E.g. 'banner' + [..., 'banner', 'banner_2'] -> 'banner_3'."""
    used = set()
    for bid in current_order:
        if bid == block_type_id:
            used.add(1)
        elif get_block_type_id(bid) == block_type_id:
            used.add(get_instance_number(bid))
    n = 1
    while n in used:
        n += 1
    return block_type_id if n == 1 else f"{block_type_id}_{n}"


def get_default_block_order():
    return [b["id"] for b in BLOCK_REGISTRY]
