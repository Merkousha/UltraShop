import random
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from decimal import Decimal
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from catalog.models import Category, DiscountCode, Product, ProductImage, ProductVariant, WarehouseStock
from core.models import Store, StoreStaff, User, Warehouse
from customers.models import Customer
from orders.models import Order, OrderLine, OrderStatusEvent


@dataclass(frozen=True)
class BusinessSeedConfig:
    label: str
    categories: list[str]
    shipping_required: bool
    base_price_range: tuple[int, int]


BUSINESS_CONFIGS: dict[str, BusinessSeedConfig] = {
    "shoes": BusinessSeedConfig(
        label="فروشگاه کفش",
        categories=["کفش ورزشی", "کفش رسمی", "صندل", "بوت", "کفش روزمره"],
        shipping_required=True,
        base_price_range=(1_500_000, 8_500_000),
    ),
    "cafe": BusinessSeedConfig(
        label="کافه و رستوران",
        categories=["قهوه", "نوشیدنی سرد", "دسر", "غذای اصلی", "پیش غذا"],
        shipping_required=False,
        base_price_range=(250_000, 1_200_000),
    ),
    "clothing": BusinessSeedConfig(
        label="فروشگاه لباس",
        categories=["تی‌شرت", "پیراهن", "شلوار", "مانتو", "اکسسوری"],
        shipping_required=True,
        base_price_range=(1_200_000, 6_500_000),
    ),
    "electronics": BusinessSeedConfig(
        label="فروشگاه لوازم الکترونیکی",
        categories=["گوشی موبایل", "لپ‌تاپ", "لوازم جانبی", "صوتی تصویری", "گجت هوشمند"],
        shipping_required=True,
        base_price_range=(2_500_000, 45_000_000),
    ),
}


class Command(BaseCommand):
    help = "Seed realistic demo data for a target store (categories, products, images, customers, orders, CRM)."

    def add_arguments(self, parser):
        parser.add_argument("--store", required=True, help="Store username (slug)")
        parser.add_argument(
            "--business",
            required=True,
            choices=sorted(BUSINESS_CONFIGS.keys()),
            help="Business type template",
        )
        parser.add_argument("--products-per-category", type=int, default=10)
        parser.add_argument("--customers", type=int, default=20)
        parser.add_argument("--orders", type=int, default=15)
        parser.add_argument("--reset", action="store_true", help="Delete existing store-scoped tenant data before seeding")
        parser.add_argument("--seed", type=int, default=1405, help="Random seed for deterministic output")

    def handle(self, *args, **options):
        store_username = options["store"].strip()
        business_key = options["business"]
        products_per_category = max(1, int(options["products_per_category"]))
        customer_count = max(1, int(options["customers"]))
        order_count = max(0, int(options["orders"]))
        do_reset = bool(options["reset"])
        random_seed = int(options["seed"])

        store = Store.objects.filter(username=store_username).select_related("owner").first()
        if not store:
            raise CommandError(f"Store '{store_username}' not found.")

        config = BUSINESS_CONFIGS[business_key]
        rng = random.Random(random_seed)

        self.stdout.write(self.style.NOTICE(f"Seeding store: {store.name} ({store.username})"))
        self.stdout.write(self.style.NOTICE(f"Business template: {config.label}"))

        with self._store_context(store):
            with transaction.atomic():
                if do_reset:
                    self._reset_store_data(store)

                warehouse = self._ensure_default_warehouse(store)
                staff = self._ensure_staff_accounts(store)
                categories = self._seed_categories(store, config)
                variants = self._seed_products(store, categories, config, products_per_category, warehouse, rng)
                customers = self._seed_customers(store, customer_count)
                self._seed_orders(store, customers, variants, order_count, config, rng)
                self._seed_crm(store, customers, staff)
                self._seed_discount_code(store)

        self.stdout.write(self.style.SUCCESS("Demo seed completed successfully."))

    @contextmanager
    def _store_context(self, store: Store):
        if not getattr(settings, "USE_DJANGO_TENANTS", False):
            with nullcontext():
                yield
            return

        try:
            from django_tenants.utils import schema_context
            from tenancy.models import Tenant
        except Exception as exc:
            raise CommandError(f"Tenant mode is enabled but tenant utilities are unavailable: {exc}")

        tenant = Tenant.objects.filter(store_slug=store.username, is_active=True).first()
        if not tenant:
            raise CommandError(
                f"No active tenant found for store '{store.username}'. Create/provision tenant first."
            )

        with schema_context(tenant.schema_name):
            yield

    def _reset_store_data(self, store: Store):
        from crm.models import ChatMessage, ChatSession, ContactActivity, Lead, SaleTask

        Order.objects.filter(store=store).delete()
        Product.objects.filter(store=store).delete()
        Category.objects.filter(store=store).delete()
        Customer.objects.filter(store=store).delete()
        DiscountCode.objects.filter(store=store).delete()
        ContactActivity.objects.filter(store=store).delete()
        SaleTask.objects.filter(store=store).delete()
        Lead.objects.filter(store=store).delete()
        ChatMessage.objects.filter(session__store=store).delete()
        ChatSession.objects.filter(store=store).delete()

    def _ensure_default_warehouse(self, store: Store):
        warehouse, created = Warehouse.objects.get_or_create(
            store=store,
            is_default=True,
            defaults={
                "name": "انبار مرکزی",
                "city": "تهران",
                "province": "تهران",
                "priority": 0,
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created default warehouse."))
        return warehouse

    def _ensure_staff_accounts(self, store: Store):
        sales_user = self._ensure_user(
            email=f"sales.{store.username}@ultra-shop.local",
            username=f"sales-{store.username}",
            first_name="کارشناس",
            last_name="فروش",
        )
        accountant_user = self._ensure_user(
            email=f"accounting.{store.username}@ultra-shop.local",
            username=f"accounting-{store.username}",
            first_name="کارشناس",
            last_name="مالی",
        )

        StoreStaff.objects.get_or_create(
            store=store,
            user=sales_user,
            defaults={"role": StoreStaff.Role.SALES_AGENT},
        )
        StoreStaff.objects.get_or_create(
            store=store,
            user=accountant_user,
            defaults={"role": StoreStaff.Role.ACCOUNTANT},
        )
        return {"sales": sales_user, "accountant": accountant_user}

    def _ensure_user(self, *, email: str, username: str, first_name: str, last_name: str):
        user = User.objects.filter(email=email).first()
        if user:
            return user
        user = User.objects.create_user(
            email=email,
            username=username,
            password="Demo@12345",
            first_name=first_name,
            last_name=last_name,
        )
        return user

    def _seed_categories(self, store: Store, config: BusinessSeedConfig):
        created = []
        for idx, name in enumerate(config.categories, start=1):
            slug_base = slugify(name, allow_unicode=True)
            slug = f"{slug_base}-{store.username}"[:220]
            category, _ = Category.objects.get_or_create(
                store=store,
                slug=slug,
                defaults={
                    "name": name,
                    "description": f"محصولات مرتبط با {name}",
                    "sort_order": idx,
                },
            )
            self._attach_remote_image(
                file_field=category.image,
                file_name=f"cat-{store.username}-{idx}.jpg",
                url=f"https://picsum.photos/seed/{store.username}-cat-{idx}/1200/1200",
            )
            created.append(category)
        self.stdout.write(self.style.SUCCESS(f"Categories ready: {len(created)}"))
        return created

    def _seed_products(self, store, categories, config, per_category, warehouse, rng):
        variants = []
        for category in categories:
            for idx in range(1, per_category + 1):
                name = self._product_name(config, category.name, idx)
                slug = self._unique_product_slug(store, name, idx)
                sku = f"{category.slug[:8].upper()}-{idx:03d}"
                product, _ = Product.objects.get_or_create(
                    store=store,
                    slug=slug,
                    defaults={
                        "name": name,
                        "description": f"{name} با کیفیت بالا و تضمین اصالت.",
                        "sku": sku,
                        "status": Product.Status.ACTIVE,
                        "requires_shipping": config.shipping_required,
                    },
                )
                product.categories.add(category)

                price = rng.randint(*config.base_price_range)
                variant, _ = ProductVariant.objects.get_or_create(
                    product=product,
                    name="استاندارد",
                    defaults={
                        "sku": f"{sku}-STD",
                        "price": price,
                        "compare_at_price": int(price * Decimal("1.15")),
                        "stock": rng.randint(10, 120),
                        "is_active": True,
                    },
                )

                WarehouseStock.objects.get_or_create(
                    warehouse=warehouse,
                    variant=variant,
                    defaults={"quantity": variant.stock, "reserved": 0},
                )

                self._ensure_product_images(product, seed_slug=f"{store.username}-{category.slug}-{idx}")
                variants.append(variant)

        self.stdout.write(self.style.SUCCESS(f"Products ready: {len(variants)} variants"))
        return variants

    def _seed_customers(self, store, customer_count):
        customers = []
        for idx in range(1, customer_count + 1):
            phone = f"09{idx:09d}"[-11:]
            customer, _ = Customer.objects.get_or_create(
                store=store,
                phone=phone,
                defaults={
                    "name": f"مشتری {idx}",
                    "email": f"customer{idx}.{store.username}@example.com",
                },
            )
            customers.append(customer)
        self.stdout.write(self.style.SUCCESS(f"Customers ready: {len(customers)}"))
        return customers

    def _seed_orders(self, store, customers, variants, order_count, config, rng):
        if not customers or not variants or order_count <= 0:
            return

        statuses = [Order.Status.PAID, Order.Status.PACKED, Order.Status.SHIPPED, Order.Status.DELIVERED, Order.Status.PENDING]

        for idx in range(order_count):
            customer = rng.choice(customers)
            status = rng.choice(statuses)
            variant = rng.choice(variants)
            quantity = rng.randint(1, 3)

            order = Order.objects.create(
                store=store,
                customer=customer,
                guest_phone=customer.phone,
                guest_name=customer.name,
                shipping_address="تهران، خیابان نمونه، پلاک ۱۰",
                shipping_city="تهران",
                shipping_province="تهران",
                shipping_postal_code=f"1{idx:09d}"[:10],
                shipping_email=customer.email,
                shipping_method="پیک" if config.shipping_required else "حضوری",
                status=status,
            )

            OrderLine.objects.create(
                order=order,
                product_name=variant.product.name,
                variant_name=variant.name,
                sku=variant.sku,
                quantity=quantity,
                unit_price=variant.price,
                product=variant.product,
                variant=variant,
            )

            OrderStatusEvent.objects.create(
                order=order,
                status=status,
                note="ایجاد سفارش نمونه توسط اسکریپت seed",
            )

    def _seed_crm(self, store, customers, staff):
        from crm.models import ContactActivity, Lead, SaleTask

        sales_user = staff.get("sales")
        for idx, customer in enumerate(customers[:10], start=1):
            lead, _ = Lead.objects.get_or_create(
                store=store,
                customer=customer,
                defaults={
                    "name": customer.name or f"سرنخ {idx}",
                    "phone": customer.phone,
                    "email": customer.email,
                    "source": "manual",
                    "assigned_to": sales_user,
                    "note": "سرنخ نمونه ایجاد شده توسط seed",
                },
            )

            ContactActivity.objects.get_or_create(
                store=store,
                customer=customer,
                lead=lead,
                activity_type=ContactActivity.ActivityType.NOTE,
                description="ارتباط اولیه با مشتری ثبت شد.",
                reference_id=f"seed-{customer.pk}",
            )

            SaleTask.objects.get_or_create(
                store=store,
                lead=lead,
                title=f"پیگیری تماس با {lead.name}",
                defaults={
                    "due_date": timezone.localdate() + timezone.timedelta(days=(idx % 4) + 1),
                    "priority": SaleTask.Priority.MEDIUM,
                    "assigned_to": sales_user,
                },
            )

    def _seed_discount_code(self, store):
        now = timezone.now()
        DiscountCode.objects.get_or_create(
            store=store,
            code="WELCOME10",
            defaults={
                "discount_type": DiscountCode.DiscountType.PERCENT,
                "value": 10,
                "min_order_amount": 500_000,
                "max_uses": 200,
                "expires_at": now + timezone.timedelta(days=60),
                "is_active": True,
            },
        )

    def _unique_product_slug(self, store, name: str, idx: int):
        base = slugify(name, allow_unicode=True)[:280]
        slug = f"{base}-{idx}"[:320]
        if not Product.objects.filter(store=store, slug=slug).exists():
            return slug
        n = 2
        while True:
            candidate = f"{slug[:300]}-{n}"[:320]
            if not Product.objects.filter(store=store, slug=candidate).exists():
                return candidate
            n += 1

    def _product_name(self, config: BusinessSeedConfig, category_name: str, idx: int):
        if "کافه" in config.label:
            return f"{category_name} ویژه {idx}"
        return f"{category_name} مدل {idx}"

    def _ensure_product_images(self, product: Product, seed_slug: str):
        if product.images.exists():
            return

        urls = [
            f"https://picsum.photos/seed/{seed_slug}-1/1200/1200",
            f"https://picsum.photos/seed/{seed_slug}-2/1200/1200",
        ]
        for idx, url in enumerate(urls, start=1):
            image = ProductImage(product=product, is_primary=(idx == 1), sort_order=idx, alt_text=product.name)
            self._attach_remote_image(
                file_field=image.image,
                file_name=f"product-{seed_slug}-{idx}.jpg",
                url=url,
                save_model=image,
            )

    def _attach_remote_image(self, *, file_field, file_name: str, url: str, save_model=None):
        # Avoid overriding existing image.
        if file_field and getattr(file_field, "name", ""):
            return

        try:
            req = Request(url, headers={"User-Agent": "UltraShopSeed/1.0"})
            with urlopen(req, timeout=15) as response:
                data = response.read()

            file_field.save(file_name, ContentFile(data), save=bool(save_model is None))
            if save_model is not None:
                save_model.save()
        except Exception:
            # Network/image failures should never break seed flow.
            return
