# backend/database.py

import os
from dotenv import load_dotenv
import motor.motor_asyncio
import redis.asyncio as aioredis

load_dotenv()

# --- MongoDB ---
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

users_collection = db["users"]
preferences_collection = db["preferences"]

# --- Redis ---
REDIS_URL = os.getenv("REDIS_URL")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

# --- Preference Helpers ---
async def get_user_preferences(user_id: str):
    prefs = await preferences_collection.find_one({"user_id": user_id})
    return prefs or {}

async def save_user_preferences(user_id: str, preferences: dict):
    await preferences_collection.update_one(
        {"user_id": user_id},
        {"$set": {"preferences": preferences}},
        upsert=True
    )
