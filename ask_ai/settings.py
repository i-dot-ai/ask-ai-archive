# mypy: ignore-errors

import os
import socket
from pathlib import Path

import environ
import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.django import DjangoIntegration

from .hosting_environment import HostingEnvironment

env = environ.Env()


if HostingEnvironment.is_test():
    load_dotenv(".env.test")
else:
    load_dotenv(".env")


SECRET_KEY = env.str("DJANGO_SECRET_KEY")
ENVIRONMENT = env.str("ENVIRONMENT")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG")

BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Application definition
INSTALLED_APPS = [
    "ask_ai.conversation",
    "automatilib.core",
    "automatilib.cola",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "single_session",
    "storages",
    "health_check",
    "health_check.db",
    "health_check.contrib.migrations",
    "health_check.cache",
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
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "ask_ai.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [
            BASE_DIR / "ask_ai" / "templates",
            BASE_DIR / "ask_ai" / "templates" / "auth",
        ],
        "OPTIONS": {"environment": "ask_ai.jinja2.environment"},
    },
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

WSGI_APPLICATION = "ask_ai.wsgi.application"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "automatilib.cola.backend.COLAAuthenticationBackend",
]

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

LANGUAGE_CODE = "en-GB"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SITE_ID = 1
AUTH_USER_MODEL = "conversation.User"

LOGIN_REDIRECT_URL = "declaration"  # Need to complete declaration on every login
LOGIN_URL = "login"

# CSP settings https://content-security-policy.com/
# https://django-csp.readthedocs.io/
CSP_DEFAULT_SRC = (
    "'self'",
    "s3.amazonaws.com",
    "ask-ai-files-dev.s3.amazonaws.com",
    "ask-ai-files-prod.s3.amazonaws.com",
    "plausible.io",
)
CSP_OBJECT_SRC = ("'none'",)
CSP_REQUIRE_TRUSTED_TYPES_FOR = ("'script'",)
CSP_FONT_SRC = (
    "'self'",
    "s3.amazonaws.com",
    "ask-ai-files-dev.s3.amazonaws.com",
    "ask-ai-files-prod.s3.amazonaws.com",
)
CSP_STYLE_SRC = (
    "'self'",
    "ask-ai-files-dev.s3.amazonaws.com",
    "ask-ai-files-prod.s3.amazonaws.com",
)
CSP_FRAME_ANCESTORS = ("'none'",)

# https://pypi.org/project/django-permissions-policy/
PERMISSIONS_POLICY: dict[str, list] = {
    "accelerometer": [],
    "autoplay": [],
    "camera": [],
    "display-capture": [],
    "encrypted-media": [],
    "fullscreen": [],
    "gamepad": [],
    "geolocation": [],
    "gyroscope": [],
    "microphone": [],
    "midi": [],
    "payment": [],
}

CSRF_COOKIE_HTTPONLY = True

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 60 * 60 * 24
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_ENGINE = "django.contrib.sessions.backends.db"


if HostingEnvironment.is_beanstalk():
    LOCALHOST = socket.gethostbyname(socket.gethostname())
    ALLOWED_HOSTS = [
        "dev.ask-ai.cabinetoffice.gov.uk",
        "ask-ai.cabinetoffice.gov.uk",
        "ask-ai-dev.eba-amn4cidw.eu-west-2.elasticbeanstalk.com",
        "ask-ai-prod.eba-amn4cidw.eu-west-2.elasticbeanstalk.com",
        LOCALHOST,
    ]

    for key, value in HostingEnvironment.get_beanstalk_environ_vars().items():
        env(key, default=value)

    STATICFILES_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME")
    INSTALLED_APPS += ["health_check.contrib.s3boto3_storage"]
    # https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features.logging.html
    LOG_ROOT = "/opt/python/log/"
    LOG_HANDLER = "file"
    SENTRY_DSN = env.str("SENTRY_DSN")
    SENTRY_ENVIRONMENT = env.str("SENTRY_ENVIRONMENT")
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
        ],
        environment=SENTRY_ENVIRONMENT,
        send_default_pii=False,
        traces_sample_rate=1.0,
        profiles_sample_rate=0.0,
    )
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    LOG_ROOT = "."
    LOG_HANDLER = "console"

if HostingEnvironment.is_local():
    # For Docker to work locally
    ALLOWED_HOSTS.append("0.0.0.0")  # nosec B104 - don't do this on server!
else:
    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security
    # Mozilla guidance max-age 2 years
    SECURE_HSTS_SECONDS = 2 * 365 * 24 * 60 * 60
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SESSION_COOKIE_SECURE = True


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("POSTGRES_DB"),
        "USER": env.str("POSTGRES_USER"),
        "PASSWORD": env.str("POSTGRES_PASSWORD"),
        "HOST": env.str("POSTGRES_HOST"),
        "PORT": "5432",
    }
}

# These are required for automatilib/COLA
COLA_COOKIE_NAME = env.str("COLA_COOKIE_NAME")
COLA_COOKIE_DOMAIN = env.str("COLA_COOKIE_DOMAIN")
COLA_COGNITO_CLIENT_ID = env.str("COLA_COGNITO_CLIENT_ID")
AWS_REGION_NAME = env.str("AWS_REGION_NAME")
COLA_COGNITO_USER_POOL_ID = env.str("COLA_COGNITO_USER_POOL_ID")
COLA_LOGIN_URL = env.str("COLA_LOGIN_URL")
CONTACT_EMAIL = env.str("CONTACT_EMAIL")
LOGIN_FAILURE_TEMPLATE_PATH = "auth/login-error.html"

OPENAI_KEY = env.str("OPENAI_KEY")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"verbose": {"format": "%(asctime)s %(levelname)s %(module)s: %(message)s"}},
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_ROOT, "application.log"),
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {"application": {"handlers": [LOG_HANDLER], "level": "DEBUG", "propagate": True}},
}
