"""
Django settings for HIMFG project.

Generado por 'django-admin startproject'.

Este archivo ha sido optimizado para separar configuraciones sensibles,
mejorar la internacionalización y documentar su uso para ambientes de
producción y desarrollo.
"""

from pathlib import Path
import os
from decouple import config, Csv
from datetime import timedelta


# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Entorno (development o production)
ENVIRONMENT = config("DJANGO_ENV", default="development")

# Clave secreta (NO dejar hardcodeada en producción)
SECRET_KEY = config("SECRET_KEY", default="clave-insegura")

DEBUG = config("DEBUG", default=True, cast=bool)

# Debug solo debe estar activado en desarrollo
if ENVIRONMENT == "production":
    # --- AJUSTES DE PRODUCCIÓN ---

    # Dominios permitidos
    origin = config("PRODUCTION_ORIGIN")
    CORS_ALLOWED_ORIGINS = [origin]
    CSRF_TRUSTED_ORIGINS = [origin]
else:
    # --- AJUSTES DE DESARROLLO ---
    dev_origins = config("DEVELOPMENT_ORIGINS", default="", cast=Csv())

    CORS_ALLOWED_ORIGINS = dev_origins
    CSRF_TRUSTED_ORIGINS = dev_origins

# Hosts permitidos
if ENVIRONMENT == "production":
    ALLOWED_HOSTS = config("ALLOWED_HOSTS_PRODUCTION_ORIGIN", cast=Csv())
else:
    ALLOWED_HOSTS = config("ALLOWED_HOSTS_DEVELOPMENT_ORIGINS", cast=Csv())

# Aplicaciones instaladas
INSTALLED_APPS = [
    "user.apps.UserConfig",  # Aplicación de gestión de usuarios
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    # Terceros
    "drf_yasg",  # Swagger
    "rest_framework",  # Django REST Framework
    "rest_framework_simplejwt",  # JWT
    "rest_framework_simplejwt.token_blacklist",  # Para revocar tokens
]

# Middleware habilitado
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Configuración del sistema de URLs
ROOT_URLCONF = "HIMFG.urls"

# Modelo de usuario personalizado
AUTH_USER_MODEL = "user.User"

# Configuración de plantillas
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # Puedes agregar rutas personalizadas si usas templates externos
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

# Configuración del servidor WSGI
WSGI_APPLICATION = "HIMFG.wsgi.application"

# Base de datos (usa SQLite por defecto, PostgreSQL en producción)
#if ENVIRONMENT == "production":
DATABASES = {
    "default": {
        "ENGINE": config("DATABASE_ENGINE"),
        "NAME": config("DATABASE_NAME"),
        "USER": config("DATABASE_USER"),
        "PASSWORD": config("DATABASE_PASSWORD"),
        "HOST": config("DATABASE_HOST"),
        "PORT": config("DATABASE_PORT"),
    }
}
#else:
#    DATABASES = {
#        "default": {
#            "ENGINE": "django.db.backends.sqlite3",
#            "NAME": BASE_DIR / "db.sqlite3",
#        }
#    }

# Validadores de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Configuraciones de internacionalización
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = '/auth-api/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Tipo de campo automático por defecto
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Configuración de Swagger para JWT
SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,
    "VALIDATOR_URL": None,
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": (
                "JWT Authorization header usando el esquema Bearer. "
                'Ejemplo: "Bearer {token}"'
            ),
        }
    },
}

# Configuración de logging para desarrollo y depuración
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "proyecto.log"),
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 2,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "user": {  # Ajustar al nombre real de la app si es diferente
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Configuración de Django REST Framework para usar JWT y filtros
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        #'user.authentication.CookieJWTAuthentication', # Se usa para extraer el access token de la cookie sin la necesidad de mandarlo al header
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "15/min",  # 15 solicitudes por minuto
    },
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
}


BASE_DIR = Path(__file__).resolve().parent.parent

with open(config("PRIVATE_KEY_PATH")) as f:
    PRIVATE_KEY = f.read()

with open(config("PUBLIC_KEY_PATH")) as f:
    PUBLIC_KEY = f.read()

# Configuración de tiempos para el Token
SIMPLE_JWT = {
    
    "ALGORITHM": "RS256",
    "SIGNING_KEY": PRIVATE_KEY,
    "VERIFYING_KEY": PUBLIC_KEY,    
    
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("ACCESS_TOKEN_LIFETIME_MINUTES", default=5, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("REFRESH_TOKEN_LIFETIME_DAYS", default=1, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,  # Crea un nuevo refresh token cada vez que se usa
    "BLACKLIST_AFTER_ROTATION": True,  # Invalida el refresh token anterior
    "UPDATE_LAST_LOGIN": True,  # Actualiza el campo last_login del usuario
    "USER_ID_FIELD": "user_id",
    "USER_ID_CLAIM": "user_id",
}

# Configuración para despliegue detrás de un proxy inverso
FORCE_SCRIPT_NAME = "/auth-api"
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')