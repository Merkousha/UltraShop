"""
Django settings for UltraShop project.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root when present (e.g. production or local overrides)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-in-production",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,.localhost,.ultrashop.local",
    ).split(",") if h.strip()
]

# CSRF: use env list if set (production), else dev defaults
_csrf_origins_env = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
if _csrf_origins_env:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins_env.split(",") if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        "http://127.0.0.1:8085",
        "http://localhost:8085",
        "http://localhost",
        "http://127.0.0.1",
    ]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "accounts",
    "stores",
    "customers",
    "catalog",
    "orders",
    "shipping",
    "payments",
    "accounting",
    "platform_admin",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "stores.middleware.StoreMiddleware",
    "customers.middleware.CustomerMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "stores.context_processors.current_store",
                "customers.context_processors.current_customer",
                "core.context_processors.platform_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database (use DATA_DIR in Docker for persistent volume)
_data_dir = os.environ.get("DATA_DIR")
if _data_dir:
    _data_path = Path(_data_dir)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(_data_path / "db.sqlite3"),
        }
    }
    MEDIA_ROOT = _data_path / "media"
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    MEDIA_ROOT = BASE_DIR / "media"

MEDIA_URL = "media/"

# Auth
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "stores:dashboard"
LOGOUT_REDIRECT_URL = "core:home"

# Internationalization
LANGUAGE_CODE = "fa"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model (email as identifier for store owners)
AUTH_USER_MODEL = "accounts.User"

# Multi-tenancy: platform root domain (no store subdomain)
PLATFORM_ROOT_DOMAIN = os.environ.get("PLATFORM_ROOT_DOMAIN", "ultrashop.local")
STORE_SUBDOMAIN_SEPARATOR = "."
# Use path-based store URLs: helpio.ir/store/number1/ instead of number1.helpio.ir (no subdomain/port)
PLATFORM_USE_PATH_BASED_STORE_URLS = os.environ.get("PLATFORM_USE_PATH_BASED_STORE_URLS", "0") == "1"

# Payment gateway: "mock" or "zarinpal"
PAYMENT_GATEWAY = os.environ.get("PAYMENT_GATEWAY", "mock")
ZARINPAL_MERCHANT_ID = os.environ.get("ZARINPAL_MERCHANT_ID", "")
ZARINPAL_SANDBOX = os.environ.get("ZARINPAL_SANDBOX", "1") == "1"

# Notifications (email)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@ultrashop.local")

# Platform commission (0 = 0%, 0.05 = 5% of order total)
PLATFORM_COMMISSION_RATE = float(os.environ.get("PLATFORM_COMMISSION_RATE", "0"))

# Production security (when DEBUG is False)
if not DEBUG:
    # Required behind Nginx/Caddy: trust X-Forwarded-Proto so Django sees HTTPS and doesn't redirect loop
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "1") == "1"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
