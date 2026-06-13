from .base import *
import dj_database_url
import urllib.parse

DEBUG = False

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') + [
    'healthcheck.railway.app',
    '.railway.app',
]

DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
}

CORS_ALLOWED_ORIGINS = [
    origin.strip() 
    for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') 
    if origin.strip()
]

FRONTEND_URL = os.environ.get('FRONTEND_URL', '')
ACCOUNT_EMAIL_CONFIRMATION_URL = FRONTEND_URL + '/portal/verify-email/{key}' if FRONTEND_URL else ''

# Redis
REDIS_URL = os.environ.get('REDIS_URL')


_redis_url = os.environ.get('REDIS_URL', '')
if _redis_url:
    _redis = urllib.parse.urlparse(_redis_url)
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
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security headers
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True