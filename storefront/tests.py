"""
Integration tests for key storefront and dashboard flows.

Covers:
  - Chat rate limit (C-06)
  - StorePlan product limit enforcement
  - Storefront cart → checkout flow
  - Order status transition + cache invalidation
"""

import json

from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from catalog.models import Product, ProductVariant
from core.models import Store, StorePlan, PlatformSettings
from core.services import check_plan_limit, PlanLimitExceeded
from customers.models import Customer
from orders.models import Order, OrderLine


def _make_store(username="teststore"):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    owner = User.objects.create_user(
        username=username + "_owner",
        email=username + "@example.com",
        password="TestPass!123",
    )
    ps, _ = PlatformSettings.objects.get_or_create(pk=1)
    store = Store.objects.create(
        name="فروشگاه تست",
        username=username,
        owner=owner,
    )
    return store, owner


def _make_product(store, name="محصول تست", price=50000):
    product = Product.objects.create(
        store=store,
        name=name,
        status=Product.Status.ACTIVE,
    )
    variant = ProductVariant.objects.create(
        product=product,
        name="پیش‌فرض",
        price=price,
        stock=10,
    )
    return product, variant


class ChatRateLimitTest(TestCase):
    """C-06: Verify that ChatView enforces the 20-message-per-session limit."""

    def setUp(self):
        self.store, self.owner = _make_store("chatratelimit")
        self.product, _ = _make_product(self.store)
        self.client = Client()

    def _chat_url(self):
        return reverse("storefront:chat", kwargs={"store_username": self.store.username})

    def _post_message(self, text="سلام"):
        return self.client.post(
            self._chat_url(),
            data=json.dumps({"message": text}),
            content_type="application/json",
        )

    def test_first_message_allowed(self):
        resp = self._post_message()
        # AI not configured → graceful fallback, not a rate-limit error
        self.assertNotEqual(resp.status_code, 429)

    def test_rate_limit_after_20_messages(self):
        from crm.models import ChatSession, ChatMessage

        # Ensure session is created
        self.client.get(reverse("storefront:home", kwargs={"store_username": self.store.username}))
        session_key = self.client.session.session_key or "test"
        chat_session, _ = ChatSession.objects.get_or_create(
            store=self.store,
            session_key=session_key,
        )
        # Create 20 user messages directly
        for i in range(20):
            ChatMessage.objects.create(
                session=chat_session,
                role=ChatMessage.Role.USER,
                content=f"پیام {i}",
            )

        resp = self._post_message("پیام ۲۱ام")
        self.assertEqual(resp.status_code, 429)
        data = resp.json()
        self.assertIn("error", data)
        self.assertIn("contact_url", data)


class StorePlanProductLimitTest(TestCase):
    """Plan 4: Verify StorePlan.max_products is enforced via check_plan_limit."""

    def setUp(self):
        self.store, _ = _make_store("planlimitstore")
        self.plan = StorePlan.objects.create(
            name="پلن آزمایشی",
            slug="test-plan",
            max_products=3,
            max_warehouses=2,
        )
        self.store.plan = self.plan
        self.store.save(update_fields=["plan"])

    def test_within_limit_passes(self):
        # 2 products exist, limit is 3 — should not raise
        _make_product(self.store, "محصول ۱")
        _make_product(self.store, "محصول ۲")
        current_count = Product.objects.filter(store=self.store).count()
        try:
            check_plan_limit(self.store, "products", current_count)
        except PlanLimitExceeded:
            self.fail("check_plan_limit raised unexpectedly when under limit")

    def test_at_limit_raises(self):
        # 3 products exist, limit is 3 — should raise
        for i in range(3):
            _make_product(self.store, f"محصول {i}")
        current_count = Product.objects.filter(store=self.store).count()
        with self.assertRaises(PlanLimitExceeded):
            check_plan_limit(self.store, "products", current_count)

    def test_no_plan_uses_default_limit(self):
        """Store without a plan should fall back to _DEFAULT_LIMITS (100 products)."""
        self.store.plan = None
        self.store.save(update_fields=["plan"])
        # 3 products is below the default limit of 100 — should pass
        for i in range(3):
            _make_product(self.store, f"محصول پیش‌فرض {i}")
        current_count = Product.objects.filter(store=self.store).count()
        try:
            check_plan_limit(self.store, "products", current_count)
        except PlanLimitExceeded:
            self.fail("check_plan_limit raised with no plan and count below default limit")


class StorefrontCartCheckoutTest(TestCase):
    """Verify basic cart add and checkout page load flow."""

    def setUp(self):
        self.store, self.owner = _make_store("cartstore")
        PlatformSettings.objects.get_or_create(pk=1, defaults={"shipping_enabled": False})
        self.product, self.variant = _make_product(self.store)
        self.client = Client()

    def test_add_to_cart(self):
        url = reverse("storefront:cart-add", kwargs={"store_username": self.store.username})
        resp = self.client.post(url, {"variant_id": self.variant.pk, "quantity": 1})
        # Should redirect to cart
        self.assertIn(resp.status_code, (200, 302))

    def test_cart_page_loads(self):
        url = reverse("storefront:cart", kwargs={"store_username": self.store.username})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_checkout_page_loads(self):
        # Add item first
        add_url = reverse("storefront:cart-add", kwargs={"store_username": self.store.username})
        self.client.post(add_url, {"variant_id": self.variant.pk, "quantity": 1})
        checkout_url = reverse("storefront:checkout", kwargs={"store_username": self.store.username})
        resp = self.client.get(checkout_url)
        self.assertIn(resp.status_code, (200, 302))


class OrderStatusCacheInvalidationTest(TestCase):
    """Plan 3: Verify analytics cache is invalidated when order status changes."""

    def setUp(self):
        self.store, self.owner = _make_store("cachestore")
        self.client = Client()
        self.client.force_login(self.owner)
        # Inject current_store into session
        session = self.client.session
        session["current_store_id"] = self.store.pk
        session.save()
        self.order = Order.objects.create(
            store=self.store,
            status=Order.Status.PENDING,
        )

    def test_cache_invalidated_on_order_status_change(self):
        # Manually set an analytics cache entry
        for days in (7, 14, 30, 60, 90):
            cache.set(f"store_analytics_{self.store.pk}_{days}", {"revenue": 999}, 900)

        url = reverse("dashboard:order-detail", kwargs={"pk": self.order.pk})
        self.client.post(url, {"new_status": "paid", "note": ""})

        # All analytics caches should now be empty
        for days in (7, 14, 30, 60, 90):
            self.assertIsNone(
                cache.get(f"store_analytics_{self.store.pk}_{days}"),
                msg=f"Cache for days={days} was not invalidated",
            )

