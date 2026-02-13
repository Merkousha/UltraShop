"""
Session-based cart: keyed by store_id. Structure:
  session["cart"] = { str(store_id): { "items": [ {"variant_id": int, "qty": int, "price": str }, ... ] } }
"""
from decimal import Decimal
from django.conf import settings

CART_SESSION_KEY = "cart"


def get_cart_for_store(session, store_id):
    cart = session.get(CART_SESSION_KEY) or {}
    return cart.setdefault(str(store_id), {"items": []})


def get_cart_items(session, store_id):
    data = get_cart_for_store(session, store_id)
    return data.get("items") or []


def set_cart_items(session, store_id, items):
    """items = list of dicts with variant_id, qty, price."""
    cart = session.get(CART_SESSION_KEY) or {}
    cart[str(store_id)] = {"items": items}
    session[CART_SESSION_KEY] = cart
    session.modified = True


def add_item(session, store_id, variant_id, qty, price):
    items = list(get_cart_items(session, store_id))
    price_str = str(price)
    for i, row in enumerate(items):
        if row.get("variant_id") == variant_id:
            items[i] = {"variant_id": variant_id, "qty": row.get("qty", 0) + qty, "price": price_str}
            set_cart_items(session, store_id, items)
            return
    items.append({"variant_id": variant_id, "qty": qty, "price": price_str})
    set_cart_items(session, store_id, items)


def remove_item(session, store_id, variant_id):
    items = [x for x in get_cart_items(session, store_id) if x.get("variant_id") != variant_id]
    set_cart_items(session, store_id, items)


def update_item_qty(session, store_id, variant_id, qty):
    if qty <= 0:
        remove_item(session, store_id, variant_id)
        return
    items = list(get_cart_items(session, store_id))
    for i, row in enumerate(items):
        if row.get("variant_id") == variant_id:
            items[i] = {**row, "qty": qty}
            set_cart_items(session, store_id, items)
            return
    set_cart_items(session, store_id, items)


def cart_total(items_with_variants):
    """items_with_variants = list of (cart_item_dict, ProductVariant). Returns Decimal total."""
    total = Decimal("0")
    for item, variant in items_with_variants:
        total += Decimal(item.get("price", 0)) * item.get("qty", 0)
    return total
