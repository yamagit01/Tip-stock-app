import environ

from .base import *

# Read .env if exists
env = environ.Env()
env.read_env(os.path.join(BASE_DIR, '.env'))


# Security settings
DEBUG = False

SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')


# Database
DATABASES = {
    'default': env.db()
}
DATABASES['default']['ATOMIC_REQUESTS'] = True


# Static files
STATIC_ROOT = '/var/www/{}/static'.format(PROJECT_NAME)

MEDIA_ROOT = '/var/www/{}/media'.format(PROJECT_NAME)


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
    # ハンドラ
    'handlers': {
        # ファイル出力用ハンドラ
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/{}/app.log'.format(PROJECT_NAME),
            'formatter': 'production',
        },
    },
    # ロガー
    'loggers': {
        # 自作アプリケーション全般のログを拾うロガー
        '': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Django本体が出すログ全般を拾うロガー
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# Email settings
EMAIL_CONFIG = env.email_url('EMAIL_URL')
vars().update(EMAIL_CONFIG)

# axes settings
AXES_META_PRECEDENCE_ORDER = [
    'HTTP_X_FORWARDED_FOR',
]