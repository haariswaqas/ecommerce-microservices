# product_service/settings.py

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [host for host in os.environ.get("ALLOWED_HOSTS", "*").split(",") if host]



INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django_filters",
    
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles", 
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "product_service.apps.products",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

ROOT_URLCONF = "product_service.urls"
WSGI_APPLICATION = "product_service.wsgi.application"
ASGI_APPLICATION = "product_service.asgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    )
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
         "product_service.apps.products.authentication.ServiceJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "SIGNING_KEY": os.environ.get("JWT_SECRET", SECRET_KEY),
    "ALGORITHM": "HS256",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
}

CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL", "True").lower() == "true"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://admin:secret@localhost:5672/")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "internal-dev-secret")
PRODUCT_SERVICE_URL = os.environ.get("PRODUCT_SERVICE_URL", "http://localhost:8000")
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://localhost:8000")
ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:8000")
SERVICE_REQUEST_TIMEOUT = int(os.environ.get("SERVICE_REQUEST_TIMEOUT", "5"))
