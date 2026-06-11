from .base import *
import dj_database_url
import urllib.parse

DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
}

FRONTEND_URL = os.environ.get('FRONTEND_URL')

ACCOUNT_EMAIL_CONFIRMATION_URL = FRONTEND_URL + '/portal/verify-email/{key}'

CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')

# Redis
REDIS_URL = os.environ.get('REDIS_URL')


_redis = urllib.parse.urlparse(REDIS_URL)
EVENTSTREAM_REDIS = {
    'host': _redis.hostname,
    'port': _redis.port or 6379,
    'db': int(_redis.path.lstrip('/') or 0),
    'password': _redis.password,
} 

CELERY_BROKER_URL = REDIS_URL

REST_AUTH = {
    'LOGIN_SERIALIZER': 'accounts.serializers.CustomLoginSerializer',
    'USER_DETAILS_SERIALIZER': 'accounts.serializers.CustomUserDetailsSerializer',
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access-token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh-token',
    'JWT_AUTH_HTTPONLY': True,   # secure in prod
    'JWT_AUTH_SECURE': True,     # HTTPS only
    'JWT_AUTH_SAMESITE': 'None',
    'JWT_SERIALIZER': 'accounts.serializers.CustomJWTSerializer',
}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST_PASSWORD = os.environ.get('RESEND_API_KEY')

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True