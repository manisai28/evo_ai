import os
from dotenv import load_dotenv
import motor.motor_asyncio
import redis.asyncio as aioredis
from pymongo import MongoClient

load_dotenv()

# ==========================================================
# --- MongoDB (Async for FastAPI) ---
# ==========================================================
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

# Async collections
users_collection = db["users"]
preferences_collection = db["preferences"]
notes_collection = db["notes"]
reminders_collection = db["reminders"]
events_collection = db["events"]
expenses_collection = db["expenses"]
semantic_collection = db["semantic_memory"]
whatsapp_tasks_collection = db["whatsapp_tasks"]

# ==========================================================
# --- Redis (Async) ---
# ==========================================================
REDIS_URL = os.getenv("REDIS_URL")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

# ==========================================================
# --- Async Helper Functions (for FastAPI + DialogueManager) ---
# ==========================================================
async def get_user_preferences(user_id: str):
    prefs = await preferences_collection.find_one({"user_id": user_id})
    return prefs or {}

async def save_user_preferences(user_id: str, preferences: dict):
    await preferences_collection.update_one(
        {"user_id": user_id},
        {"$set": {"preferences": preferences}},
        upsert=True
    )

# --- Notes ---
async def get_user_notes(user_id: str, limit=10):
    cursor = notes_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def save_user_note(user_id: str, content: str, timestamp=None):
    from datetime import datetime
    note = {
        "user_id": user_id,
        "content": content,
        "timestamp": timestamp or datetime.now()
    }
    result = await notes_collection.insert_one(note)
    return result.inserted_id

# --- Reminders (Hybrid Approach) ---
async def get_user_reminders(user_id: str, limit=10):
    cursor = reminders_collection.find({"user_id": user_id}).sort("created", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def save_user_reminder(user_id: str, text: str, time: str, scheduled_time=None, celery_task_id=None, created=None):
    from datetime import datetime
    reminder = {
        "user_id": user_id,
        "text": text,
        "time": time,  # Original time string from user
        "scheduled_time": scheduled_time or datetime.now(),  # Exact datetime for triggering
        "celery_task_id": celery_task_id,  # Track Celery task ID
        "is_triggered": False,
        "created": created or datetime.now()
    }
    result = await reminders_collection.insert_one(reminder)
    return str(result.inserted_id)

async def delete_user_reminder(user_id: str, reminder_id: str):
    from bson.objectid import ObjectId
    result = await reminders_collection.delete_one({"user_id": user_id, "_id": ObjectId(reminder_id)})
    return result.deleted_count > 0

async def get_pending_reminders():
    from datetime import datetime
    cursor = reminders_collection.find({
        "scheduled_time": {"$lte": datetime.now()},
        "is_triggered": False
    })
    return await cursor.to_list(length=100)

async def mark_reminder_triggered(reminder_id: str):
    from bson.objectid import ObjectId
    result = await reminders_collection.update_one(
        {"_id": ObjectId(reminder_id)},
        {"$set": {"is_triggered": True}}
    )
    return result.modified_count > 0

async def update_reminder_celery_task(reminder_id: str, celery_task_id: str):
    from bson.objectid import ObjectId
    result = await reminders_collection.update_one(
        {"_id": ObjectId(reminder_id)},
        {"$set": {"celery_task_id": celery_task_id}}
    )
    return result.modified_count > 0

# --- Events ---
async def get_user_events(user_id: str, limit=10):
    cursor = events_collection.find({"user_id": user_id}).sort("created", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def save_user_event(user_id: str, name: str, time: str, created=None):
    from datetime import datetime
    event = {
        "user_id": user_id,
        "name": name,
        "time": time,
        "created": created or datetime.now()
    }
    result = await events_collection.insert_one(event)
    return result.inserted_id

# --- Expenses ---
async def get_user_expenses(user_id: str, limit=10):
    cursor = expenses_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def save_user_expense(user_id: str, amount: float, description: str, timestamp=None):
    from datetime import datetime
    expense = {
        "user_id": user_id,
        "amount": amount,
        "description": description,
        "timestamp": timestamp or datetime.now()
    }
    result = await expenses_collection.insert_one(expense)
    return result.inserted_id

async def get_total_expenses(user_id: str):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    result = await expenses_collection.aggregate(pipeline).to_list(length=1)
    return result[0]["total"] if result else 0.0

# ==========================================================
# --- Sync MongoDB (for Celery tasks) ---
# ==========================================================
sync_client = MongoClient(MONGO_URI)
sync_db = sync_client[MONGO_DB]

# Sync collections
sync_notes_collection = sync_db["notes"]
sync_reminders_collection = sync_db["reminders"]
sync_events_collection = sync_db["events"]
sync_expenses_collection = sync_db["expenses"]
sync_whatsapp_tasks_collection = sync_db["whatsapp_tasks"]
sync_music_collection = sync_db["music_history"]
# ==========================================================
# --- Sync Helper Functions (for Celery Tasks) ---
# ==========================================================
def get_user_notes_sync(user_id: str, limit=10):
    cursor = sync_notes_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    return list(cursor)

def save_user_note_sync(user_id: str, content: str, timestamp=None):
    from datetime import datetime
    note = {
        "user_id": user_id,
        "content": content,
        "timestamp": timestamp or datetime.now()
    }
    result = sync_notes_collection.insert_one(note)
    return str(result.inserted_id)

def get_user_reminders_sync(user_id: str, limit=10):
    cursor = sync_reminders_collection.find({"user_id": user_id}).sort("created", -1).limit(limit)
    return list(cursor)

def save_user_reminder_sync(user_id: str, text: str, time: str, scheduled_time=None, celery_task_id=None, created=None):
    from datetime import datetime
    reminder = {
        "user_id": user_id,
        "text": text,
        "time": time,
        "scheduled_time": scheduled_time or datetime.now(),
        "celery_task_id": celery_task_id,
        "is_triggered": False,
        "created": created or datetime.now()
    }
    result = sync_reminders_collection.insert_one(reminder)
    return str(result.inserted_id)

def delete_user_reminder_sync(user_id: str, reminder_id: str):
    from bson.objectid import ObjectId
    result = sync_reminders_collection.delete_one({"user_id": user_id, "_id": ObjectId(reminder_id)})
    return result.deleted_count > 0

def get_user_events_sync(user_id: str, limit=10):
    cursor = sync_events_collection.find({"user_id": user_id}).sort("created", -1).limit(limit)
    return list(cursor)

def save_user_event_sync(user_id: str, name: str, time: str, created=None):
    from datetime import datetime
    event = {
        "user_id": user_id,
        "name": name,
        "time": time,
        "created": created or datetime.now()
    }
    result = sync_events_collection.insert_one(event)
    return str(result.inserted_id)

def get_user_expenses_sync(user_id: str, limit=10):
    cursor = sync_expenses_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
    return list(cursor)

def save_user_expense_sync(user_id: str, amount: float, description: str, timestamp=None):
    from datetime import datetime
    expense = {
        "user_id": user_id,
        "amount": amount,
        "description": description,
        "timestamp": timestamp or datetime.now()
    }
    result = sync_expenses_collection.insert_one(expense)
    return str(result.inserted_id)

def get_total_expenses_sync(user_id: str):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    result = list(sync_expenses_collection.aggregate(pipeline))
    return result[0]["total"] if result else 0.0

def get_pending_reminders_sync():
    from datetime import datetime
    cursor = sync_reminders_collection.find({
        "scheduled_time": {"$lte": datetime.now()},
        "is_triggered": False
    })
    return list(cursor)

def mark_reminder_triggered_sync(reminder_id: str):
    from bson.objectid import ObjectId
    result = sync_reminders_collection.update_one(
        {"_id": ObjectId(reminder_id)},
        {"$set": {"is_triggered": True}}
    )
    return result.modified_count > 0

def update_reminder_celery_task_sync(reminder_id: str, celery_task_id: str):
    from bson.objectid import ObjectId
    result = sync_reminders_collection.update_one(
        {"_id": ObjectId(reminder_id)},
        {"$set": {"celery_task_id": celery_task_id}}
    )
    return result.modified_count > 0

def save_user_notification_sync(user_id: str, message: str, notification_type: str = "reminder"):
    from datetime import datetime
    notification = {
        "user_id": user_id,
        "message": message,
        "type": notification_type,
        "created": datetime.now(),
        "is_read": False
    }
    # Use existing sync_reminders_collection (or create sync_notifications_collection if you prefer)
    result = sync_reminders_collection.insert_one(notification)
    return str(result.inserted_id)

def get_user_notifications_sync(user_id: str, limit=10):
    cursor = sync_reminders_collection.find({
        "user_id": user_id,
        "type": "reminder"
    }).sort("created", -1).limit(limit)
    return list(cursor)