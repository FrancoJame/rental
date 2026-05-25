import os
from pathlib import Path
import dj_database_url
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================
# SECURITY
# ==========================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-yi#wzwry7e$=xr6#6)ruf85b6!8g7j38)*h#dhhcid&s2@b3l$')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,rental-murex-iota.vercel.app,.vercel.app,dreamhouse-ug.vercel.app',
    cast=Csv()
)

CSRF_TRUSTED_ORIGINS = [
    'https://rental-murex-iota.vercel.app',
    'https://dreamhouse-ug.vercel.app',
]

# ==========================================
# INSTALLED APPS
# ==========================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'listings',
    'cloudinary',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    'https://dreamhouse-ug.vercel.app',
    'https://rental-murex-iota.vercel.app',
]
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'housing_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'housing_project.wsgi.application'

# ==========================================
# DATABASE — Neon PostgreSQL
# ==========================================
# Neon requires sslmode=require. We parse the URL and enforce SSL via OPTIONS.
_DATABASE_URL = os.environ.get('DATABASE_URL') or config('DATABASE_URL', default=None)

if _DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=_DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # Enforce SSL for Neon — required for channel_binding to work
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS']['sslmode'] = 'require'
else:
    # Local SQLite fallback
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'listings.User'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# ==========================================
# PASSWORD VALIDATION
# ==========================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================================
# INTERNATIONALISATION
# ==========================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Kampala'
USE_I18N = True
USE_TZ = True

# ==========================================
# STATIC & MEDIA FILES
# ==========================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoiseStorage — works without a pre-built manifest (safe for Vercel)
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Cloudinary — credentials from environment variables only (never hardcoded)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'

# ==========================================
# SECURITY (production only)
# ==========================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# ==========================================
# EMAIL
# ==========================================
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@dreamhouse.ug')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='mutebifrancis33@gmail.com')

SESSION_COOKIE_AGE = 3600
