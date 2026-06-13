import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bismak.settings.prod')

app = Celery('bismak')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()