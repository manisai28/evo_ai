from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis as broker and backend
celery_app = Celery(
    'ai_assistant',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Celery configuration with updated settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_disable_rate_limits=True,
    
    # Fix the deprecation warning
    broker_connection_retry_on_startup=True,
    
    # Task routes
    task_routes={
        'backend.tasks.*': {'queue': 'ai_tasks'},
    }
)

# Import all task modules
celery_app.autodiscover_tasks([
    'backend.tasks.calculator_tasks',
    # 'backend.tasks.email_tasks',
    'backend.tasks.event_tasks',
    'backend.tasks.expense_tasks',
    'backend.tasks.news_tasks',
    'backend.tasks.notes_tasks',
    'backend.tasks.reminder_tasks',
    'backend.tasks.search_tasks',
    'backend.tasks.translate_tasks',
    'backend.tasks.weather_tasks',
])