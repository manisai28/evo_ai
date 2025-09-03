# backend/celery_app.py
import os
from celery import Celery
from dotenv import load_dotenv

# Load .env file
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "backend",  # 👈 better name than "tasks"
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Serialization settings
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

# 👇 Ensure Celery knows about your tasks
celery_app.autodiscover_tasks(["backend.tasks"])

# Or, alternatively:
# import backend.tasks  # noqa: F401
