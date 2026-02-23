"""
SO-46: Resolve layout blocks for storefront rendering.
"""
from core.blocks import get_block_by_id, get_default_block_order
from core.models import LayoutConfiguration


def get_layout_blocks(store, page_type="home"):
    """
    Return list of block dicts for the given store and page_type.
    Each item: { "id", "template", "settings", "products" (if product_grid), "categories" (if category_grid) }
    """
    try:
        layout = LayoutConfiguration.objects.get(store=store, page_type=page_type)
    except LayoutConfiguration.DoesNotExist:
        return []  # No layout config → use legacy template content

    order = layout.block_order or get_default_block_order()
    settings_map = layout.block_settings or {}
    enabled_map = layout.block_enabled or {}

    blocks_data = []
    for block_id in order:
        if enabled_map.get(block_id, True) is False:
            continue
        meta = get_block_by_id(block_id)
        if not meta:
            continue
        block_settings = {**(meta.get("default_settings") or {}), **(settings_map.get(block_id) or {})}
        block_data = {
            "id": block_id,
            "template": meta["template"],
            "settings": block_settings,
        }
        if block_id == "product_grid":
            from catalog.models import Product
            limit = int(block_settings.get("limit") or 8)
            block_data["products"] = list(
                Product.objects.filter(store=store, status="active")
                .prefetch_related("images", "variants")[:limit]
            )
        elif block_id == "category_grid":
            from catalog.models import Category
            block_data["categories"] = list(
                Category.objects.filter(store=store, parent__isnull=True)
            )
        blocks_data.append(block_data)

    return blocks_data
