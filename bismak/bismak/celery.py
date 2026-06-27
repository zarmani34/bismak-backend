import os
from celery import Celery
from pathlib import Path
from dotenv import load_dotenv

# Load .env before Django setup
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bismak.settings.prod')

app = Celery('bismak')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()