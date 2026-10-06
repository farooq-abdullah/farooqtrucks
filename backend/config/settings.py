"""Settings for a stateless trip-planning API."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only-change-before-hosting")
if not DEBUG and SECRET_KEY == "local-development-only-change-before-hosting":
    raise RuntimeError("Set DJANGO_SECRET_KEY before running in production.")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "trips",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]
# No users, sessions, saved trips, or ORM queries in this version.
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5180,http://127.0.0.1:5180"
).split(",")
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "30/hour", "location_search": "60/min"},
}
USE_TZ = True
TIME_ZONE = "UTC"
# Fallback when local coordinate-based timezone lookup returns no zone.
LOG_UTC_OFFSET = os.getenv("LOG_UTC_OFFSET", "-06:00")
DEFAULT_DEPARTURE_HOUR = 8
LOCATION_SEARCH_BASE_URL = os.getenv("LOCATION_SEARCH_BASE_URL", "https://photon.komoot.io")
GEOCODING_PROVIDER = os.getenv("GEOCODING_PROVIDER", "photon")
GEOCODING_BASE_URL = os.getenv("GEOCODING_BASE_URL", LOCATION_SEARCH_BASE_URL)
OSRM_BASE_URL = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")
MAP_USER_AGENT = os.getenv("MAP_USER_AGENT", "TripLogAssessment/0.1 (local assessment development)")
DATA_UPLOAD_MAX_MEMORY_SIZE = 32_768
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

# Serve the built React app and API on one origin in production.
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
STATIC_URL = "/assets/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [FRONTEND_DIST / "assets"] if (FRONTEND_DIST / "assets").exists() else []
STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"}}
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIST],
        "APP_DIRS": False,
    }
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
