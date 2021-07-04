import environ
import requests

from .base import *

# Read .env if exists
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env'))


# Security settings
DEBUG = False

SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Fargate用(ALBがHealthCheckでlocalIPを使用するので追加)
EC2_PRIVATE_IP = None
METADATA_URI = os.environ.get('ECS_CONTAINER_METADATA_URI_V4')

try:
    resp = requests.get(METADATA_URI)
    container_metadata = resp.json()
    EC2_PRIVATE_IP = container_metadata['Networks'][0]['IPv4Addresses'][0]
except:
    pass

if EC2_PRIVATE_IP:
    ALLOWED_HOSTS.append(EC2_PRIVATE_IP)

INSTALLED_APPS = ["storages"] + INSTALLED_APPS

# Database
DATABASES = {
    'default': env.db()
}
DATABASES['default']['ATOMIC_REQUESTS'] = True


# Logging
LOGGING = {
    # バージョンは「1」固定
    'version': 1,
    # 既存のログ設定を無効化しない
    'disable_existing_loggers': False,
    # ログフォーマット
    'formatters': {
        # 本番用
        'production': {
            'format': '%(asctime)s [%(levelname)s] %(process)d %(thread)d '
                      '%(pathname)s:%(lineno)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'production',
        },
    },
    'loggers': {
        # 自作アプリケーション全般のログを拾うロガー
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Django本体が出すログ全般を拾うロガー
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}


# Email settings
EMAIL_CONFIG = env.email_url('EMAIL_URL')
vars().update(EMAIL_CONFIG)

# axes settings
AXES_META_PRECEDENCE_ORDER = [
    'HTTP_X_FORWARDED_FOR',
]

# aws settings
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_CLOUDFRONT_DOMAIN = os.environ.get('AWS_CLOUDFRONT_DOMAIN')
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
# s3 static settings
AWS_STATIC_LOCATION = 'static'
STATIC_URL = f'https://{AWS_CLOUDFRONT_DOMAIN}/{AWS_STATIC_LOCATION}/'
STATICFILES_STORAGE = 'config.storage_backends.PublicStaticStorage'
# s3 public media settings
AWS_MEDIA_LOCATION = 'media'
MEDIA_URL = f'https://{AWS_CLOUDFRONT_DOMAIN}/{AWS_MEDIA_LOCATION}/'
DEFAULT_FILE_STORAGE = 'config.storage_backends.PublicMediaStorage'