# backend/memory/mongo_memory.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.database import (
    preferences_collection,
    notes_collection,
    semantic_collection,
)
from bson import ObjectId

class MongoMemory:
    def __init__(self,
                 prefs_col=preferences_collection,
                 notes_col=notes_collection,
                 semantic_col=semantic_collection):
        self.prefs = prefs_col
        self.notes = notes_col
        self.semantic = semantic_col

    # Preferences
    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        doc = await self.prefs.find_one({"user_id": user_id})
        return doc.get("preferences", {}) if doc else {}

    async def save_preferences(self, user_id: str, preferences: dict):
        await self.prefs.update_one(
            {"user_id": user_id},
            {"$set": {"preferences": preferences, "updated_at": datetime.utcnow()}},
            upsert=True
        )

    # Notes / Long-term memory
    async def save_note(self, user_id: str, text: str, meta: Optional[dict] = None) -> str:
        doc = {
            "user_id": user_id,
            "text": text,
            "meta": meta or {},
            "timestamp": datetime.utcnow()
        }
        res = await self.notes.insert_one(doc)
        return str(res.inserted_id)

    async def get_notes(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = self.notes.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        return results

    # Generic find/update helpers
    async def find(self, collection, query: dict, limit: int = 20):
        cursor = collection.find(query).limit(limit)
        return await cursor.to_list(length=limit)
