"""
Django settings for ultrashop project.
"""

import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-*d-w5ltw&%!&2fb3_ox&$ez2nyb=!m33(r@62-)dxaa!^szh79",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")
USE_DJANGO_TENANTS = os.environ.get("USE_DJANGO_TENANTS", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")
if "helpio.ir" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS += ["helpio.ir", "www.helpio.ir"]
if "ultrashop.darkube.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("ultrashop.darkube.app")

# CSRF trusted origins (scheme + host[:port]) for form POSTs from these domains
_trusted_hosts = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "*").split(",") if h.strip() and h.strip() != "*"]
if "helpio.ir" not in _trusted_hosts:
    _trusted_hosts += ["helpio.ir", "www.helpio.ir"]
if "ultrashop.darkube.app" not in _trusted_hosts:
    _trusted_hosts.append("ultrashop.darkube.app")
CSRF_TRUSTED_ORIGINS = []
for host in _trusted_hosts:
    if host in ("localhost", "127.0.0.1"):
        CSRF_TRUSTED_ORIGINS.append(f"http://{host}:8080")
    else:
        CSRF_TRUSTED_ORIGINS.append(f"https://{host}")
# Dev: when using default ALLOWED_HOSTS or DEBUG, allow local server (runserver 8080)
if not CSRF_TRUSTED_ORIGINS or DEBUG:
    for origin in ("http://127.0.0.1:8080", "http://localhost:8080"):
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

AUTH_USER_MODEL = "core.User"

if USE_DJANGO_TENANTS:
    SHARED_APPS = (
        "django_tenants",
        "tenancy",
        # Keep custom user model app before admin/auth migration graph issues.
        "core",
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.humanize",
        "jalali_date",
        # Shared project apps (public schema)
        "platform_admin",
        "dashboard",
    )

    TENANT_APPS = (
        # Tenant-scoped apps
        "catalog",
        "customers",
        "orders",
        "shipping",
        "accounting",
        "payments",
        "storefront",
        "crm",
    )

    INSTALLED_APPS = list(SHARED_APPS) + [a for a in TENANT_APPS if a not in SHARED_APPS]
else:
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.humanize",
        "jalali_date",
        # Project apps
        "core",
        "catalog",
        "customers",
        "orders",
        "shipping",
        "accounting",
        "payments",
        "platform_admin",
        "dashboard",
        "storefront",
        "crm",
    ]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.ThemeCSPMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.CSPMiddleware",
    "core.middleware.StoreMiddleware" if not USE_DJANGO_TENANTS else "tenancy.middleware.URLPathTenantMiddleware",
]

ROOT_URLCONF = "ultrashop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.platform_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "ultrashop.wsgi.application"

# Cache (for theme CSS per store; use Redis in production if needed)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ultrashop-default",
    }
}
THEME_CSS_CACHE_TIMEOUT = 300  # seconds (5 min)

# Database
# Priority:
# 1) DATABASE_URL / POSTGRES_URL (PostgreSQL)
# 2) sqlite fallback via DJANGO_DB_PATH
database_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")

if database_url and database_url.startswith(("postgres://", "postgresql://")):
    parsed = urlparse(database_url)
    query = parse_qs(parsed.query)
    db_engine = "django.db.backends.postgresql"
    if USE_DJANGO_TENANTS:
        db_engine = "django_tenants.postgresql_backend"

    DATABASES = {
        "default": {
            "ENGINE": db_engine,
            "NAME": (parsed.path or "").lstrip("/"),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "localhost",
            "PORT": str(parsed.port or 5432),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
        }
    }

    sslmode = os.environ.get("DB_SSLMODE") or (query.get("sslmode", [""])[0])
    if sslmode:
        DATABASES["default"]["OPTIONS"] = {"sslmode": sslmode}

    # Safety guard: block accidental use of PostgreSQL system databases by default.
    block_system_db = os.environ.get("BLOCK_SYSTEM_POSTGRES_DB", "True").lower() in ("true", "1", "yes")
    if block_system_db and DATABASES["default"]["NAME"] in {"postgres", "template0", "template1"}:
        raise RuntimeError(
            "Unsafe DATABASE_URL: system PostgreSQL database is blocked. "
            "Set a dedicated app database name, or set BLOCK_SYSTEM_POSTGRES_DB=False intentionally."
        )
else:
    if USE_DJANGO_TENANTS:
        raise RuntimeError("USE_DJANGO_TENANTS=True requires PostgreSQL DATABASE_URL/POSTGRES_URL")
    # Database path: set DJANGO_DB_PATH in Docker to persist db (e.g. /app/data/db.sqlite3)
    _db_path = os.environ.get("DJANGO_DB_PATH")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": _db_path if _db_path else str(BASE_DIR / "db.sqlite3"),
        }
    }

if USE_DJANGO_TENANTS:
    TENANT_MODEL = "tenancy.Tenant"
    TENANT_DOMAIN_MODEL = "tenancy.Domain"
    PUBLIC_SCHEMA_NAME = "public"
    TENANT_PATH_PREFIX = os.environ.get("TENANT_PATH_PREFIX", "s")
    DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Allow same-origin iframe preview inside dashboard page editor.
X_FRAME_OPTIONS = "SAMEORIGIN"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"

# Platform
PLATFORM_DOMAIN = os.environ.get("PLATFORM_DOMAIN", "localhost:8000")
PLATFORM_COMMISSION_RATE = float(os.environ.get("PLATFORM_COMMISSION_RATE", "0.05"))
PAYMENT_GATEWAY = os.environ.get("PAYMENT_GATEWAY", "mock")

# Email
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@ultra-shop.com")
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Field-level encryption key (for PA-15 sensitive fields)
FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY", SECRET_KEY[:32])

