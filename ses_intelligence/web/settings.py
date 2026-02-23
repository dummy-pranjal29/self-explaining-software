"""
SES Intelligence Embedded Web Server Settings

Minimal Django settings for the embedded web dashboard.
No external settings required - works standalone as a pip-installed package.
"""

import os
import logging
from pathlib import Path

# Try to get version from parent package, fallback to default
try:
    from ses_intelligence import __version__ as SES_VERSION
except ImportError:
    SES_VERSION = "1.0.0b1"

# ------------------------------------------------------------------
# BASE CONFIGURATION
# ------------------------------------------------------------------

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'ses-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

# Allowed hosts - configurable via environment
_allowed_hosts_env = os.environ.get('ALLOWED_HOSTS', '')
if _allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Application definition - minimal for embedded server
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'ses_intelligence.web',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

# Root URL configuration
ROOT_URLCONF = 'ses_intelligence.web.urls'

# No templates needed for API-only response
TEMPLATES = []

# WSGI application (not used directly but required)
WSGI_APPLICATION = 'ses_intelligence.web.wsgi.application'

# ------------------------------------------------------------------
# DATABASE CONFIGURATION
# ------------------------------------------------------------------
# SQLite disabled - use file-based storage instead

DATABASES = {}

# ------------------------------------------------------------------
# STATIC FILES CONFIGURATION
# ------------------------------------------------------------------

# URL prefix for static files
STATIC_URL = '/static/'

# Find the package directory for static files
PACKAGE_DIR = Path(__file__).resolve().parent

# Static root (where collectstatic will put files) - not used in embedded mode
STATIC_ROOT = None

# Additional locations to find static files - point to package static directory
STATICFILES_DIRS = [
    str(PACKAGE_DIR / 'static'),
]

# WhiteNoise for serving static files in production
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
] + MIDDLEWARE

# Use WhiteNoise storage for compressed static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ------------------------------------------------------------------
# INTERNATIONALIZATION
# ------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------
# LOGGING CONFIGURATION
# ------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "ses_intelligence": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": True,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# ------------------------------------------------------------------
# LLM CONFIGURATION (for chat endpoint)
# ------------------------------------------------------------------

# OpenAI API Key (can also be set via OPENAI_API_KEY env var)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# LLM Model (default: gpt-4o-mini for cost efficiency)
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

# ------------------------------------------------------------------
# SESSION AND CSRF (not needed for API-only but kept for compatibility)
# ------------------------------------------------------------------

# No sessions needed for API-only
SESSION_ENGINE = None

# Allow cross-origin for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ------------------------------------------------------------------
# DEFAULT AUTO FIELD
# ------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
