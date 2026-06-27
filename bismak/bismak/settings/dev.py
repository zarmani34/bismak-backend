from .base import *
from dotenv import load_dotenv

load_dotenv(BASE_DIR / '.env')


DEBUG = True

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-key')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.0.181']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {'timeout': 20},
    }
}

ACCOUNT_EMAIL_VERIFICATION = 'none'  # Disable email verification in development

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

ACCOUNT_EMAIL_CONFIRMATION_URL = FRONTEND_URL + '/portal/verify-email/{key}'

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://192.168.43.215:3000',
    'http://172.20.10.4:3000',
    'http://192.168.0.181:3000',
]

# Redis
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


# EVENTSTREAM_REDIS = {
#     'host': 'localhost',
#     'port': 6379,
#     'db': 0,
# }

CELERY_BROKER_URL = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = False  # set to True if you don't want to run a worker locally

REST_AUTH = {
    'LOGIN_SERIALIZER': 'accounts.serializers.CustomLoginSerializer',
    'USER_DETAILS_SERIALIZER': 'accounts.serializers.CustomUserDetailsSerializer',
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access-token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh-token',
    'JWT_AUTH_HTTPONLY': False,
    'JWT_AUTH_SECURE': False,
    'JWT_AUTH_SAMESITE': None,
    'JWT_SERIALIZER': 'accounts.serializers.CustomJWTSerializer',
}

EVENTSTREAM_REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
}

# Prints emails to terminal instead of sending them
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'