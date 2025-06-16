# config/settings.py

from django.core.exceptions import ImproperlyConfigured
from decouple import config
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool)

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    CSRF_TRUSTED_ORIGINS = ['https://autovise-99770207782d.herokuapp.com']


hosts = config("ALLOWED_HOSTS", default="")
ALLOWED_HOSTS = [h.strip() for h in hosts.split(",") if h.strip()]

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Application Definition

INSTALLED_APPS = [
    # Core
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # Social Login
    'allauth.socialaccount.providers.google',
    # Apps
    'apps.products',
    'apps.orders',
    'apps.users.apps.UsersConfig',
    'apps.pages',
    'apps.assets',
    # External Libraries
    'storages',
    'widget_tweaks',
    'ckeditor',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'allauth.account.middleware.AccountMiddleware',
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
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.products.context_processors.all_categories',
                'apps.orders.context_processors.cart_data',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


JAZZMIN_SETTINGS = {
    "site_title": "Autovise Admin",
    "site_header": "Autovise Admin Panel",
    "site_brand": "Autovise",
    "site_logo": None,
    "welcome_sign": "Welcome to the Autovise Admin Dashboard",
    "copyright": "Autovise Ltd",

    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    "order_with_respect_to": ["products", "orders", "users", "pages"],

    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": [
            "auth.view_user"
        ]},
    ],

    "icons": {
        "products.Product": "fas fa-box-open",
        "products.Bundle": "fas fa-cubes",
        "products.Category": "fas fa-list",
        "products.Subcategory": "fas fa-layer-group",
        "products.ProductType": "fas fa-tags",
        "products.Tag": "fas fa-tag",
        "orders.Order": "fas fa-receipt",
        "pages.NewsletterSubscriber": "fas fa-envelope",
        "users.UserProfile": "fas fa-user-circle",
    },

    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "products.product": "horizontal_tabs",
        "products.bundle": "horizontal_tabs",
    },

    "related_modal_active": True,
    "theme": "flatly",
    "show_bookmarks": True,
}


# Stripe Credentials
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", cast=str)
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", cast=str)
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", cast=str)

# Ensure none are missing
for var in (
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
):
    if not globals()[var]:
        raise ImproperlyConfigured(f"Missing required environment variable: {var}")


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },

    'loggers': {
        # capture everything from django-allauth
        'allauth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # optionally, if you want socialaccount internals too
        'allauth.socialaccount': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },

    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


SITE_ID = 2


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

EMAIL_BACKEND = config('EMAIL_BACKEND')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

SEND_ORDER_CONFIRMATION_EMAIL = config(
    'SEND_ORDER_CONFIRMATION_EMAIL',
    default=True,
    cast=bool,
)
USE_CELERY_FOR_EMAIL = config(
    'USE_CELERY_FOR_EMAIL',
    default=False,
    cast=bool,
)

ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/m",
}


LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

SOCIALACCOUNT_AUTO_SIGNUP = True   # Skip extra final step for social signups
SOCIALACCOUNT_QUERY_EMAIL = True    # Ensure email is queried from provider
SOCIALACCOUNT_LOGIN_ON_GET = True   # Login immediately after social login
SOCIALACCOUNT_LOGIN_REDIRECT_URL = "/"

GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET')

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {
            "access_type": "online",
            "prompt": "select_account"
        },
        "OAUTH_PKCE_ENABLED": True
    }
}

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 250,
        'width': 'auto',
    }
}


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/London'

USE_TZ = True

USE_I18N = True


# AWS Credentials
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='eu-west-2')
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False

AWS_S3_CUSTOM_DOMAIN = config(
    'AWS_S3_CUSTOM_DOMAIN',
    default=f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
)

MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
