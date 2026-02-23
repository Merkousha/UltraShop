"""
SO-46: Block registry for drag & drop page editor.
Each block has: id, label (Persian), template path, default settings.
"""

BLOCK_REGISTRY = [
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
    },
    {
        "id": "faq",
        "label": "سؤالات متداول",
        "template": "storefront/blocks/faq.html",
        "default_settings": {"title": "سوالات متداول", "items": []},
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


def get_block_by_id(block_id):
    for b in BLOCK_REGISTRY:
        if b["id"] == block_id:
            return b
    return None


def get_default_block_order():
    return [b["id"] for b in BLOCK_REGISTRY]
