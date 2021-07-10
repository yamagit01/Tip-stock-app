import environ

from .base import *

# Read .env if exists
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env'))

# Security settings
DEBUG = False

SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = ['*']


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tipstock',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}


# Logging
LOGGING = {}


# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'testsmedia')
STATICFILES_STORAGE = 'config.storage_backends.CollectStaticStorage'


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
BCC_EMAIL = 'test@test.com'
