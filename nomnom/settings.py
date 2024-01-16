"""
Django settings for nomnom project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path

import bleach.sanitizer
from django.utils.translation import gettext_lazy as _
from environ import bool_var, config, group, to_config, var
from icecream import install

install()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def comma_separated_string(env_val: str) -> list[str]:
    return [v.strip() for v in env_val.strip().split(",") if v.strip()]


try:
    import debug_toolbar  # noqa

    debug_toolbar_app = "debug_toolbar"
    debug_toolbar_middleware = "debug_toolbar.middleware.DebugToolbarMiddleware"
except ImportError:
    debug_toolbar_app = None
    debug_toolbar_middleware = None


@config(prefix="NOM")
class AppConfig:
    convention_app = var(default=None)

    @config
    class DB:
        name = var()
        host = var()
        port = var(5432, converter=int)
        user = var()
        password = var()

    @config
    class REDIS:
        host = var()
        port = var(6379, converter=int)

    @config
    class EMAIL:
        host = var()
        port = var(587, converter=int)
        host_user = var(default=None)
        host_password = var(default=None)
        use_tls = bool_var(default=True)

    @config
    class CONVENTION:
        hugo_packet = var(default=False)

    @config
    class SENTRY_SDK:
        dsn = var(default=None)
        environment = var(default="production")

    debug = bool_var(default=False)
    sentry_sdk = group(SENTRY_SDK)
    db = group(DB)
    redis = group(REDIS)
    email = group(EMAIL)

    @config
    class OAUTH:
        key = var()
        secret = var()
        backend = var("nomnom.social_core.ClydeOAuth2")

    oauth = group(OAUTH)

    secret_key = var()

    static_file_root = var(BASE_DIR / "staticfiles")

    allowed_hosts: list[str] = var("", converter=comma_separated_string)

    allow_username_login: bool = bool_var(False)

    convention = group(CONVENTION)


cfg = to_config(AppConfig)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = cfg.secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = cfg.debug
TEMPLATE_DEBUG = cfg.debug
DEBUG_TOOLBAR_ENABLED = debug_toolbar_app is not None
INTERNAL_IPS = ["127.0.0.1"] if DEBUG_TOOLBAR_ENABLED else []


class InvalidStringShowWarning(str):
    def __mod__(self, other):
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            f"In template, undefined variable or unknown value for: '{other}'"
        )
        return ""

    def __bool__(self):  # if using Python 2, use __nonzero__ instead
        # make the template tag `default` use its fallback value
        return False


ALLOWED_HOSTS = cfg.allowed_hosts

CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS] if ALLOWED_HOSTS else []

# Application definition

INSTALLED_APPS = [
    i
    for i in [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        # use whitenoise to serve static files, instead of django's builtin
        "whitenoise.runserver_nostatic",
        "django.contrib.staticfiles",
        # deferred tasks
        "django_celery_results",
        "django_celery_beat",
        # debug helper
        "django_extensions",
        "django_browser_reload",
        # to render markdown to HTML in templates
        "markdownify.apps.MarkdownifyConfig",
        # OAuth login
        "social_django",
        # Theming
        "django_bootstrap5",
        "fontawesomefree",
        # A healthcheck
        "watchman",
        # Template debugging
        debug_toolbar_app,
        # the convention theme; this MUST come before the nominate app, so that its templates can
        # override the nominate ones.
        cfg.convention_app,
        # The nominating and voting app
        "nominate",
        # The Hugo Awards packet application, if enabled.
        "hugopacket" if cfg.convention.hugo_packet else None,
    ]
    if i
]

# NomNom configuration
NOMNOM_ALLOW_USERNAME_LOGIN_FOR_MEMBERS = cfg.allow_username_login

# part of Six and Five
NOMNOM_HUGO_NOMINATION_COUNT = 5

AUTHENTICATION_BACKENDS = [
    cfg.oauth.backend,
    # Uncomment following if you want to access the admin
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    m
    for m in [
        debug_toolbar_middleware,
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "oauth2_provider.middleware.OAuth2TokenMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
        "django_browser_reload.middleware.BrowserReloadMiddleware",
        "social_django.middleware.SocialAuthExceptionMiddleware",
    ]
    if m
]

ROOT_URLCONF = "nomnom.urls"

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
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "nominate.context_processors.site",
            ],
            "string_if_invalid": InvalidStringShowWarning("%s"),
        },
    },
]

WSGI_APPLICATION = "nomnom.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": cfg.db.name,
        "USER": cfg.db.user,
        "PASSWORD": cfg.db.password,
        "HOST": cfg.db.host,
        "PORT": str(cfg.db.port),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{cfg.redis.host}:{cfg.redis.port}",
    },
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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

LOGOUT_REDIRECT_URL = "election:index"

# we are using postgres, so this is recommended in the docs.
SOCIAL_AUTH_JSONFIELD_ENABLED = True

SOCIAL_AUTH_CLYDE_KEY = cfg.oauth.key
SOCIAL_AUTH_CLYDE_SECRET = cfg.oauth.secret
SOCIAL_AUTH_CLYDE_LOGIN_REDIRECT_URL = "/"
SOCIAL_AUTH_CLYDE_USER_FIELD_MAPPING = {
    "full_name": "first_name",
    "email": "email",
}
# Can't use the backend-specific one because of https://github.com/python-social-auth/social-core/issues/875
# SOCIAL_AUTH_CLYDE_LOGIN_ERROR_URL = "nominate:login_error"
SOCIAL_AUTH_LOGIN_ERROR_URL = "election:login_error"

SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ["username", "first_name", "email"]

SOCIAL_AUTH_CLYDE_PIPELINE = [
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "nominate.social_auth.pipeline.get_wsfs_permissions",
    "nominate.social_auth.pipeline.set_user_wsfs_membership",
    "nominate.social_auth.pipeline.add_election_permissions",
]
# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"
LANGUAGES = [
    ("en", _("English")),
    ("zh", _("Chinese")),
]

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = cfg.static_file_root

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Async tasks
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "default"
CELERY_BROKER_URL = f"redis://{cfg.redis.host}:{cfg.redis.port}"
CELERY_TIMEZONE = "America/Los_Angeles"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Presentation
MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": bleach.sanitizer.ALLOWED_TAGS | {"p", "h4", "h5"},
    }
}

BOOTSTRAP5 = {
    "field_renderers": {
        "default": "django_bootstrap5.renderers.FieldRenderer",
        "blank-safe": "nominate.renderers.BlankSafeFieldRenderer",
    },
}

# Email
EMAIL_HOST = cfg.email.host
EMAIL_PORT = cfg.email.port
EMAIL_HOST_USER = cfg.email.host_user
EMAIL_HOST_PASSWORD = cfg.email.host_password
EMAIL_USE_TLS = cfg.email.use_tls

# Sentry
if cfg.sentry_sdk.dsn is not None:
    # settings.py
    import sentry_sdk

    sentry_sdk.init(
        dsn=cfg.sentry_sdk.dsn,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        # Our environment
        environment=cfg.sentry_sdk.environment,
    )

    # api = falcon.API()

try:
    from .settings_override import *  # noqa: F403
except ImportError:
    ...
