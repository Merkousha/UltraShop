from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from catalog.models import Category, DiscountCode, Product, ProductVariant
from core.models import PlatformSettings, Store
from customers.models import AbandonedCart
from orders.models import Order, OrderLine


class StoreMixin:
    """Resolve store from URL slug."""

    def dispatch(self, request, *args, **kwargs):
        self.store = get_object_or_404(Store, username=kwargs["store_username"], is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["store"] = self.store
        from core.models import StoreTheme
        theme, _ = StoreTheme.objects.get_or_create(store=self.store)
        ctx["store_theme"] = theme
        return ctx


class StoreHomeView(StoreMixin, TemplateView):
    template_name = "storefront/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from core.layout_service import get_layout_blocks
        ctx["layout_blocks"] = get_layout_blocks(self.store, "home")
        ctx["categories"] = Category.objects.filter(store=self.store, parent__isnull=True)
        ctx["featured_products"] = Product.objects.filter(
            store=self.store, status="active"
        ).prefetch_related("images", "variants")[:12]
        return ctx


class CategoryListView(StoreMixin, ListView):
    template_name = "storefront/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.filter(store=self.store, parent__isnull=True)


class CategoryDetailView(StoreMixin, TemplateView):
    template_name = "storefront/category_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category"] = get_object_or_404(
            Category, store=self.store, slug=self.kwargs["slug"]
        )
        ctx["products"] = Product.objects.filter(
            store=self.store, status="active", categories=ctx["category"]
        ).prefetch_related("images", "variants")
        return ctx


class ProductDetailView(StoreMixin, TemplateView):
    template_name = "storefront/product_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = get_object_or_404(
            Product, store=self.store, slug=self.kwargs["slug"], status="active"
        )
        return ctx


# ─── C-04: Product Search ─────────────────────────────────
class ProductSearchView(StoreMixin, ListView):
    template_name = "storefront/search_results.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        if not q:
            return Product.objects.none()
        return Product.objects.filter(
            store=self.store,
            status="active",
        ).filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q)
        ).prefetch_related("images", "variants")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


# ─── Cart (session-based) ────────────────────────────────
def _get_cart(request):
    """Return cart dict: {str(variant_pk): quantity}."""
    return request.session.get("cart", {})


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def _cart_items(store, cart):
    """Resolve cart dict to list of dicts with variant & product info."""
    items = []
    total = 0
    for variant_pk_str, qty in cart.items():
        try:
            variant = ProductVariant.objects.select_related("product").get(
                pk=int(variant_pk_str), product__store=store
            )
            line_total = variant.price * qty
            total += line_total
            items.append({
                "variant": variant,
                "product": variant.product,
                "quantity": qty,
                "line_total": line_total,
            })
        except (ProductVariant.DoesNotExist, ValueError):
            pass
    return items, total


class CartView(StoreMixin, TemplateView):
    """Show cart contents."""
    template_name = "storefront/cart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cart = _get_cart(self.request)
        items, total = _cart_items(self.store, cart)
        ctx["cart_items"] = items
        ctx["cart_total"] = total
        return ctx


class CartAddView(StoreMixin, View):
    """POST: add a product variant to the session cart."""

    def post(self, request, *args, **kwargs):
        variant_id = request.POST.get("variant_id")
        try:
            quantity = max(1, int(request.POST.get("quantity", 1)))
        except (ValueError, TypeError):
            quantity = 1

        try:
            variant = ProductVariant.objects.get(
                pk=int(variant_id), product__store=self.store, product__status="active"
            )
        except (ProductVariant.DoesNotExist, ValueError, TypeError):
            return redirect("storefront:cart", store_username=self.store.username)

        cart = _get_cart(request)
        key = str(variant.pk)
        cart[key] = cart.get(key, 0) + quantity
        _save_cart(request, cart)
        return redirect("storefront:cart", store_username=self.store.username)


class CartRemoveView(StoreMixin, View):
    """POST: remove an item from the session cart."""

    def post(self, request, *args, **kwargs):
        variant_id = request.POST.get("variant_id")
        cart = _get_cart(request)
        key = str(variant_id)
        if key in cart:
            del cart[key]
            _save_cart(request, cart)
        return redirect("storefront:cart", store_username=self.store.username)


class CheckoutView(StoreMixin, TemplateView):
    """GET: show checkout form. POST: place order."""
    template_name = "storefront/checkout.html"

    def _needs_shipping(self, cart):
        """Return True if any cart product requires shipping AND platform shipping is enabled."""
        ps = PlatformSettings.load()
        if not ps.shipping_enabled:
            return False
        for variant_pk_str in cart:
            try:
                variant = ProductVariant.objects.select_related("product").get(
                    pk=int(variant_pk_str), product__store=self.store
                )
                if variant.product.requires_shipping:
                    return True
            except (ProductVariant.DoesNotExist, ValueError):
                pass
        return False

    def _save_abandoned_cart(self, request, cart, phone="", email=""):
        """Persist cart snapshot to AbandonedCart for recovery."""
        if not cart:
            return
        session_key = request.session.session_key or ""
        if not session_key:
            request.session.save()
            session_key = request.session.session_key or ""
        if not session_key:
            return
        defaults = {
            "cart_data": cart,
            "recovered": False,
        }
        if phone:
            defaults["phone"] = phone
        if email:
            defaults["email"] = email
        AbandonedCart.objects.update_or_create(
            store=self.store,
            session_key=session_key,
            recovered=False,
            defaults=defaults,
        )

    def _mark_cart_recovered(self, request):
        """Mark the AbandonedCart as recovered once an order is placed."""
        session_key = request.session.session_key or ""
        if session_key:
            AbandonedCart.objects.filter(
                store=self.store,
                session_key=session_key,
                recovered=False,
            ).update(recovered=True)

    def _validate_discount(self, code_str, cart_total):
        """
        Validate discount code against the store and cart total.
        Returns (DiscountCode, discount_amount) or (None, 0) with an error message.
        """
        now = timezone.now()
        try:
            dc = DiscountCode.objects.get(store=self.store, code__iexact=code_str, is_active=True)
        except DiscountCode.DoesNotExist:
            return None, 0, "کد تخفیف نامعتبر است."
        if dc.expires_at and dc.expires_at < now:
            return None, 0, "کد تخفیف منقضی شده است."
        if dc.max_uses is not None and dc.used_count >= dc.max_uses:
            return None, 0, "ظرفیت استفاده از این کد تخفیف تمام شده است."
        if cart_total < dc.min_order_amount:
            return None, 0, f"حداقل مبلغ سفارش برای این کد {dc.min_order_amount:,} ریال است."
        discount_amount = dc.compute_discount(cart_total)
        return dc, discount_amount, ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cart = _get_cart(self.request)
        items, total = _cart_items(self.store, cart)
        ctx["cart_items"] = items
        ctx["cart_total"] = total
        ctx["needs_shipping"] = self._needs_shipping(cart)
        ctx["discount_amount"] = 0
        ctx["discount_error"] = ""
        ctx["discount_code"] = ""
        ctx["final_total"] = total
        return ctx

    def get(self, request, *args, **kwargs):
        cart = _get_cart(request)
        if cart:
            self._save_abandoned_cart(request, cart)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        cart = _get_cart(request)
        if not cart:
            return redirect("storefront:cart", store_username=self.store.username)

        items, total = _cart_items(self.store, cart)
        if not items:
            return redirect("storefront:cart", store_username=self.store.username)

        needs_shipping = self._needs_shipping(cart)
        guest_name = request.POST.get("name", "").strip()
        guest_phone = request.POST.get("phone", "").strip()

        # ── Discount code ───────────────────────────────────────────
        discount_amount = 0
        discount_obj = None
        discount_error = ""
        code_str = request.POST.get("discount_code", "").strip()
        if code_str:
            discount_obj, discount_amount, discount_error = self._validate_discount(code_str, total)
            if discount_error:
                # Re-render checkout with error
                ctx = self.get_context_data()
                ctx["discount_error"] = discount_error
                ctx["discount_code"] = code_str
                return self.render_to_response(ctx)

        final_total = max(0, total - discount_amount)

        # ── Save abandoned cart with phone before creating order ─────
        self._save_abandoned_cart(request, cart, phone=guest_phone)

        order = Order.objects.create(
            store=self.store,
            guest_name=guest_name,
            guest_phone=guest_phone,
            shipping_address=request.POST.get("address", "").strip() if needs_shipping else "",
            shipping_city=request.POST.get("city", "").strip() if needs_shipping else "",
            shipping_province=request.POST.get("province", "").strip() if needs_shipping else "",
            shipping_postal_code=request.POST.get("postal_code", "").strip() if needs_shipping else "",
            status=Order.Status.PENDING,
            discount_code_used=code_str,
            discount_amount=discount_amount,
        )

        for item in items:
            OrderLine.objects.create(
                order=order,
                product=item["product"],
                variant=item["variant"],
                product_name=item["product"].name,
                variant_name=item["variant"].name,
                sku=item["variant"].sku,
                quantity=item["quantity"],
                unit_price=item["variant"].price,
            )

        # ── Consume discount code usage ──────────────────────────────
        if discount_obj:
            DiscountCode.objects.filter(pk=discount_obj.pk).update(used_count=discount_obj.used_count + 1)

        # ── Mark abandoned cart as recovered ─────────────────────────
        self._mark_cart_recovered(request)

        # Clear cart
        _save_cart(request, {})

        return redirect("storefront:order-confirm", store_username=self.store.username, pk=order.pk)


class OrderConfirmView(StoreMixin, TemplateView):
    """Show order confirmation page."""
    template_name = "storefront/order_confirm.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["order"] = get_object_or_404(Order, pk=self.kwargs["pk"], store=self.store)
        return ctx


class ChatView(StoreMixin, View):
    """
    POST JSON API endpoint for storefront AI chat.
    Returns {"reply": "..."} or {"error": "..."}.
    """

    def post(self, request, *args, **kwargs):
        import json as _json
        from core.ai_service import AIError, chat_with_products, search_products_for_chat
        from crm.models import ChatMessage, ChatSession

        try:
            body = _json.loads(request.body)
        except (ValueError, TypeError):
            body = {}

        user_message = (body.get("message") or "").strip()
        if not user_message:
            return JsonResponse({"error": "پیام خالی است."}, status=400)

        # Ensure session key exists
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key or "anonymous"

        # Get or create chat session
        chat_session, _ = ChatSession.objects.get_or_create(
            store=self.store,
            session_key=session_key,
        )

        # Load last 10 messages for context
        past_msgs = list(
            chat_session.messages.order_by("-created_at").values("role", "content")[:10]
        )
        past_msgs.reverse()

        # Build message list for AI
        ai_messages = [{"role": m["role"], "content": m["content"]} for m in past_msgs]
        ai_messages.append({"role": "user", "content": user_message})

        # RAG: search products for the user query
        product_context = search_products_for_chat(user_message, self.store)

        # Call AI
        try:
            reply = chat_with_products(ai_messages, product_context, self.store)
        except AIError as e:
            # Graceful fallback when AI is not configured
            reply = "متأسفانه در حال حاضر دستیار هوشمند در دسترس نیست. لطفاً از طریق تماس با فروشگاه راهنمایی بگیرید."

        # Persist messages
        ChatMessage.objects.create(session=chat_session, role=ChatMessage.Role.USER, content=user_message)
        ChatMessage.objects.create(session=chat_session, role=ChatMessage.Role.ASSISTANT, content=reply)

        # Update session timestamp
        chat_session.save(update_fields=["updated_at"])

        return JsonResponse({"reply": reply})

