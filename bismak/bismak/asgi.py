"""
ASGI config for bismak project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bismak.settings.dev')

from django.core.asgi import get_asgi_application


application = get_asgi_application()
