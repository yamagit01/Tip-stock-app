import environ

from .base import *

# Read .env if exists
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env'))

# Security settings
DEBUG = True

SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = ['*']


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUESTS': True,
    }
}


# Logging
LOGGING = {}


# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'testsmedia')


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
