from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

raw_secret = os.getenv("SECRET_KEY")
if not raw_secret:
    raise RuntimeError("SECRET_KEY is missing. Add it to your .env file so Django can start safely.")
SECRET_KEY = raw_secret
DEBUG = os.getenv("DEBUG", "True").strip().lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

BASIC_ADMIN_PASSWORD = os.getenv("BASIC_ADMIN_PASSWORD", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "anymail",
    "barbers",
    "bookings.apps.BookingsConfig",
    "contact",
    "reviews",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "meister"),
        "USER": os.getenv("DB_USER", "meister"),
        "PASSWORD": os.getenv("DB_PASS", "meister123"),
        "HOST": os.getenv("DB_HOST", "db"),
        "PORT": os.getenv("DB_PORT", "3306"),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Berlin")
USE_I18N = True
USE_TZ = True

STATIC_URL = os.getenv("STATIC_URL", "/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = os.getenv("MEDIA_URL", "/media/")
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Meister Barbershop API",
    "DESCRIPTION": "Booking API",
    "VERSION": "1.0.0",
}

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
CORS_ALLOWED_ORIGINS = ALLOWED_ORIGINS
CORS_ALLOW_ALL_ORIGINS = False if ALLOWED_ORIGINS else True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email Configuration (Transactional Provider with DKIM or Gmail SMTP fallback)
EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', '').lower()  # mailgun, sendgrid, or empty for Gmail

if EMAIL_PROVIDER == 'mailgun':
    EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
    ANYMAIL = {
        'MAILGUN_API_KEY': os.getenv('EMAIL_API_KEY', ''),
        'MAILGUN_SENDER_DOMAIN': os.getenv('EMAIL_DOMAIN', 'meisterbarbershop.de'),
        'MAILGUN_API_URL': os.getenv('MAILGUN_API_URL', 'https://api.eu.mailgun.net/v3'),  # EU region
    }
elif EMAIL_PROVIDER == 'sendgrid':
    EMAIL_BACKEND = 'anymail.backends.sendgrid.EmailBackend'
    ANYMAIL = {
        'SENDGRID_API_KEY': os.getenv('EMAIL_API_KEY', ''),
    }
else:
    # Fallback to Gmail SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'meister.barbershop.erlangen@gmail.com')
    EMAIL_HOST_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', os.getenv('EMAIL_HOST_PASSWORD', ''))

DEFAULT_FROM_EMAIL = os.getenv('EMAIL_FROM', os.getenv('DEFAULT_FROM_EMAIL', 'Meister Barbershop <no-reply@meisterbarbershop.de>'))
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Google Reviews Configuration
GOOGLE_PLACE_ID = os.getenv('GOOGLE_PLACE_ID', 'ChIJRWUULEz5oUcRhfnp-cp0dXs')

# Site Configuration
SITE_URL = os.getenv('SITE_URL', 'https://www.meisterbarbershop.de')
SITE_IMPRINT_URL = os.getenv('SITE_IMPRINT_URL', f'{SITE_URL}/impressum')
SITE_PRIVACY_URL = os.getenv('SITE_PRIVACY_URL', f'{SITE_URL}/datenschutz')

# Email System Configuration
FOLLOWUP_EMAIL_COOLDOWN_DAYS = int(os.getenv('FOLLOWUP_EMAIL_COOLDOWN_DAYS', '60'))

# Telegram Alerts Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Twilio SMS Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '')

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'email_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/meister-email.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'meister.email': {
            'handlers': ['email_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
