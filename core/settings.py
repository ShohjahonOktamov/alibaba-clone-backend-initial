import os
import sys
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.append(os.path.join(BASE_DIR, 'apps'))

SECRET_KEY = config("SECRET_KEY", default="hjg^&%**%%^*GHVGJHGKJGKH", cast=str)

DEBUG = config("DEBUG", default=False, cast=bool)

if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = ["*"]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

EXTERNAL_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",
    "django_redis"
]

LOCAL_APPS = [
    "user",
    "share",
    "product"
]

INSTALLED_APPS = DJANGO_APPS + EXTERNAL_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = "core.wsgi.application"

# Database

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default='db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
    }
}

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)

STATIC_URL: str = "static/"
STATIC_ROOT: Path = BASE_DIR / "static"

MEDIA_URL: str = '/media/'
MEDIA_ROOT: Path = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS: list[str] = [
    "user.backends.CustomJWTAuthentication"
]

AUTH_USER_MODEL: str = "user.User"

BIRTH_YEAR_MIN: int = 1900
BIRTH_YEAR_MAX: int = datetime.now().year

# email

EMAIL_BACKEND: str = config('EMAIL_BACKEND', default="django.core.mail.backends.smtp.EmailBackend", cast=str)
EMAIL_HOST: str = config('EMAIL_HOST', default="smtp.gmail.com", cast=str)
EMAIL_USE_TLS: bool = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_PORT: str = config('EMAIL_PORT', default="587", cast=str)
EMAIL_HOST_USER: str = config('EMAIL_HOST_USER', default='@', cast=str)
EMAIL_HOST_PASSWORD: str = config('EMAIL_HOST_PASSWORD', default='*', cast=str)

# redis setup

REDIS_HOST: str = config("REDIS_HOST", default="localhost", cast=str)
REDIS_PORT: str = config("REDIS_PORT", default=6379, cast=int)
REDIS_DB: str = config("REDIS_DB", default=0, cast=int)

REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

CACHES: dict[str, dict[str, str | dict[str, str]]] = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

SESSION_ENGINE: str = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS: str = "default"

# celery setup
CELERY_BROKER_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

CELERY_RESULT_BACKEND: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

CELERY_TIMEZONE: str = TIME_ZONE

CELERY_TASKS_ALWAYS_EAGER: bool = False

# stripe setup


# rest_framework setup

REST_FRAMEWORK: dict[str, list[str] | str | int] = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'user.backends.CustomJWTAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 10,
}

# jwt setup

SIMPLE_JWT: dict[str, timedelta | bool | str | None | tuple[str]] = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=10),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=10),
}

# DRF Spectacular

SPECTACULAR_SETTINGS = {
    "TITLE": "Alibaba Clone API",
    "DESCRIPTION": "API documentation for Alibaba Clone Backend",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SORT_OPERATIONS": False,
    "TAGS": [
        {
            "name": "Users and Auth Management API",
            "description": "API for Users and Auth Management"
        },
        {
            "name": "Products Management API",
            "description": "API for Products and Categories Management"
        },
        # {
        #     "name": "Templates Management API",
        #     "description": "API for Templates Management"
        # }
    ]
}

# logging setup
