from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 DEBUG: Trying non-SSL connection...")

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', '6379')
redis_username = os.getenv('REDIS_USERNAME', '')
redis_password = os.getenv('REDIS_PASSWORD', '')

# Try without SSL first to test basic connectivity
redis_url = f"redis://{redis_username}:{redis_password}@{redis_host}:{redis_port}/0"

print(f"🔍 DEBUG: Non-SSL Redis URL = {redis_url.replace(redis_password, '***') if redis_password else redis_url}")

celery_app = Celery(
    'ai_assistant',
    broker=redis_url,
    backend=redis_url
)

# Rest of your config...
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_disable_rate_limits=True,
    task_routes={
        'backend.tasks.*': {'queue': 'ai_tasks'},
    },
    beat_schedule={
        'check-missed-reminders-every-10-minutes': {
            'task': 'backend.tasks.reminder_tasks.check_missed_reminders',
            'schedule': 600.0,
        },
    }
)

celery_app.autodiscover_tasks([
    'backend.tasks.calculator_tasks',
    'backend.tasks.event_tasks',
    'backend.tasks.expense_tasks',
    'backend.tasks.news_tasks',
    'backend.tasks.notes_tasks',
    'backend.tasks.reminder_tasks',
    'backend.tasks.search_tasks',
    'backend.tasks.translate_tasks',
    'backend.tasks.weather_tasks',
    'backend.tasks.whatsapp_tasks',
    'backend.tasks.music_tasks',
])

print("🔍 DEBUG: Non-SSL configuration complete")