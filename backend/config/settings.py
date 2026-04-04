"""
Django settings for ChandaMama Retail Dashboard
Production-hardened with django-environ + full logging
"""
import os
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ['*']),
    CORS_ALLOW_ALL_ORIGINS=(bool, True),
)
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY    = env('SECRET_KEY', default='django-insecure-chandamama-default-key-2026!')
DEBUG         = env('DEBUG', default=True)
ALLOWED_HOSTS = env('ALLOWED_HOSTS', default=['*'])

INSTALLED_APPS = [
    'django_prometheus',   # ← add at TOP
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'store',
    'rest_framework',
    'corsheaders',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',  # ← FIRST
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.getenv('POSTGRES_DB',       env('POSTGRES_DB',       default='myeod_db')),
        'USER':     os.getenv('POSTGRES_USER',     env('POSTGRES_USER',     default='postgres')),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', env('POSTGRES_PASSWORD', default='')),
        'HOST':     os.getenv('DB_HOST',           env('DB_HOST',           default='db')),
        'PORT':     os.getenv('DB_PORT',           env('DB_PORT',           default='5432')),
        'OPTIONS':  {'connect_timeout': 10},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

TWILIO_ACCOUNT_SID     = os.getenv('TWILIO_ACCOUNT_SID',     env('TWILIO_ACCOUNT_SID',     default=''))
TWILIO_AUTH_TOKEN      = os.getenv('TWILIO_AUTH_TOKEN',      env('TWILIO_AUTH_TOKEN',      default=''))
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', env('TWILIO_WHATSAPP_NUMBER', default='whatsapp:+14155238886'))
OWNER_WHATSAPP_NUMBER  = os.getenv('OWNER_WHATSAPP_NUMBER',  env('OWNER_WHATSAPP_NUMBER',  default=''))

CORS_ALLOW_ALL_ORIGINS = env('CORS_ALLOW_ALL_ORIGINS', default=True)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER      = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    X_FRAME_OPTIONS                = 'DENY'
    SESSION_COOKIE_SECURE          = True
    CSRF_COOKIE_SECURE             = True
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ── Logging ───────────────────────────────────────────────────────
log_dir = BASE_DIR / 'logs'
log_dir.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format':  '[{asctime}] {levelname} {module} — {message}',
            'style':   '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format':  '[{asctime}] {levelname} — {message}',
            'style':   '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'error_file': {
            'level':       'ERROR',
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    str(log_dir / 'error.log'),
            'maxBytes':    5 * 1024 * 1024,
            'backupCount': 3,
            'formatter':   'verbose',
        },
        'request_file': {
            'level':       'INFO',
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    str(log_dir / 'requests.log'),
            'maxBytes':    10 * 1024 * 1024,
            'backupCount': 5,
            'formatter':   'simple',
        },
        'security_file': {
            'level':       'WARNING',
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    str(log_dir / 'security.log'),
            'maxBytes':    5 * 1024 * 1024,
            'backupCount': 3,
            'formatter':   'verbose',
        },
        'console': {
            'class':     'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers':  ['error_file', 'console'],
            'level':     'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers':  ['request_file', 'console'],
            'level':     'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers':  ['security_file', 'console'],
            'level':     'WARNING',
            'propagate': False,
        },
        'store': {
            'handlers':  ['error_file', 'console'],
            'level':     'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level':    'WARNING',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'