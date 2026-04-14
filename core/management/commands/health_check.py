from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from core.models import Store


class Command(BaseCommand):
    help = "Run a lightweight health check for database and tenant store schemas."

    def add_arguments(self, parser):
        parser.add_argument("--store-id", type=int, default=None, help="Check only one store by primary key.")
        parser.add_argument(
            "--store-username",
            type=str,
            default=None,
            help="Check only one store by username.",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Return a non-zero exit code if any check fails.",
        )
        parser.add_argument(
            "--skip-tenancy",
            action="store_true",
            help="Skip tenant schema checks even when django-tenants mode is enabled.",
        )

    def handle(self, *args, **options):
        failures = []

        self.stdout.write("[1/4] Checking database connectivity...")
        failures.extend(self._check_database_connection())

        self.stdout.write("[2/4] Checking stores...")
        stores = self._get_stores(options)
        failures.extend(self._check_store_selection(stores, options))

        self.stdout.write("[3/4] Checking tenancy...")
        if getattr(settings, "USE_DJANGO_TENANTS", False) and not options["skip_tenancy"]:
            failures.extend(self._check_tenant_schemas(stores))
        else:
            self.stdout.write("  - Skipped tenant schema checks")

        self.stdout.write("[4/4] Checking core table availability...")
        failures.extend(self._check_core_tables())

        if failures:
            for failure in failures:
                self.stderr.write(self.style.ERROR(failure))
            summary = f"Health check completed with {len(failures)} issue(s)."
            if options["strict"]:
                raise CommandError(summary)
            self.stdout.write(self.style.WARNING(summary))
        else:
            self.stdout.write(self.style.SUCCESS("Health check completed successfully."))

    def _check_database_connection(self):
        failures = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.stdout.write(self.style.SUCCESS("  - Database connection: OK"))
        except Exception as exc:
            failures.append(f"Database connection failed: {exc}")
        return failures

    def _get_stores(self, options):
        stores = Store.objects.filter(is_active=True).order_by("pk")
        store_id = options.get("store_id")
        store_username = options.get("store_username")
        if store_id:
            stores = stores.filter(pk=store_id)
        if store_username:
            stores = stores.filter(username=store_username)
        return list(stores)

    def _check_store_selection(self, stores, options):
        failures = []
        if stores:
            self.stdout.write(self.style.SUCCESS(f"  - Active stores matched: {len(stores)}"))
            return failures

        message = "No active stores matched the given filters."
        if options.get("store_id") or options.get("store_username"):
            failures.append(message)
            return failures

        self.stdout.write(self.style.WARNING("  - No active stores found"))
        return failures

    def _check_tenant_schemas(self, stores):
        failures = []
        try:
            from django_tenants.utils import schema_context
            from tenancy.models import Tenant
        except ImportError as exc:
            failures.append(f"django-tenants is not available: {exc}")
            return failures

        required_tables = [
            "products",
            "categories",
            "orders",
            "customers",
            "payments",
            "shipments",
        ]

        for store in stores:
            tenant = Tenant.objects.filter(store_slug=store.username, is_active=True).first()
            if not tenant:
                failures.append(f"Store {store.pk} ({store.username}) has no active tenant schema.")
                continue

            try:
                with schema_context(tenant.schema_name):
                    table_names = set(connection.introspection.table_names())
            except Exception as exc:
                failures.append(
                    f"Failed to inspect tenant schema '{tenant.schema_name}' for store {store.pk}: {exc}"
                )
                continue

            missing = [table for table in required_tables if table not in table_names]
            if missing:
                failures.append(
                    f"Tenant schema '{tenant.schema_name}' is missing tables: {', '.join(missing)}"
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  - Tenant schema {tenant.schema_name} for store {store.username}: OK"
                    )
                )

        return failures

    def _check_core_tables(self):
        failures = []
        if getattr(settings, "USE_DJANGO_TENANTS", False):
            self.stdout.write("  - Core tables are checked via tenant schemas in this mode")
            return failures

        required_tables = [
            "products",
            "categories",
            "orders",
            "customers",
            "payments",
            "shipments",
        ]
        table_names = set(connection.introspection.table_names())
        missing = [table for table in required_tables if table not in table_names]
        if missing:
            failures.append(f"Database is missing tables: {', '.join(missing)}")
        else:
            self.stdout.write(self.style.SUCCESS("  - Core tables: OK"))
        return failures