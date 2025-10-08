# backend/memory/memory_manager.py
import json
import datetime
from typing import List, Dict, Any
from backend.core.database import redis_client, preferences_collection, notes_collection, semantic_collection
from bson import ObjectId

# Semantic embeddings
from sentence_transformers import SentenceTransformer
import numpy as np


class MemoryManager:
    def __init__(self):
        self.short_term_prefix = "stm:"
        self.long_term_prefix = "ltm:"
        self.model = SentenceTransformer("all-MiniLM-L6-v2")  # Embedding model

    # ==========================================================
    # --- SHORT-TERM MEMORY (Redis)
    # ==========================================================
    async def append_to_session(self, session_key: str, message: Dict[str, Any]):
        """Append a message to user's current short-term session."""
        key = f"{self.short_term_prefix}{session_key}"
        await redis_client.rpush(key, json.dumps(message))
        await redis_client.ltrim(key, -10, -1)  # Keep only recent 10
        await redis_client.expire(key, 3600)    # Expire in 1 hour

    async def get_session_conversation(self, user_id: str, session_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent short-term messages."""
        key = f"{self.short_term_prefix}{session_key}"
        data = await redis_client.lrange(key, -limit, -1)
        return [json.loads(item) for item in data] if data else []

    async def clear_short_term(self, session_key: str):
        await redis_client.delete(f"{self.short_term_prefix}{session_key}")

    # ==========================================================
    # --- LONG-TERM MEMORY (MongoDB)
    # ==========================================================
    async def store_long_term_memory(self, user_id: str, facts: List[Dict[str, Any]]):
        """Store extracted facts or important details into MongoDB."""
        for fact in facts:
            doc = {
                "user_id": user_id,
                "type": fact.get("type", "fact"),
                "key": fact.get("key"),
                "value": fact.get("value"),
                "source": fact.get("source", "assistant"),
                "timestamp": datetime.datetime.utcnow(),
                "text": f"{fact.get('key')}: {fact.get('value')}"
            }
            await notes_collection.insert_one(doc)
            # Store semantic embedding separately
            await self.store_semantic_memory(user_id, doc["text"])

    async def get_long_term(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve last N long-term notes."""
        cursor = notes_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        notes = await cursor.to_list(length=limit)
        return notes

    # ==========================================================
    # --- SEMANTIC MEMORY METHODS
    # ==========================================================
    async def store_semantic_memory(self, user_id: str, text: str):
        """Store text with embeddings for semantic search."""
        embedding = self.model.encode(text).tolist()
        doc = {
            "user_id": user_id,
            "text": text,
            "embedding": embedding,
            "timestamp": datetime.datetime.utcnow()
        }
        await semantic_collection.insert_one(doc)

    async def retrieve_semantic_memory(self, user_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve top-k semantically similar memories."""
        query_vec = self.model.encode(query)
        cursor = semantic_collection.find({"user_id": user_id})
        all_notes = await cursor.to_list(length=100)

        # Cosine similarity
        def cosine(a, b):
            a = np.array(a)
            b = np.array(b)
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        scored = []
        for note in all_notes:
            score = cosine(note["embedding"], query_vec)
            scored.append((score, note["text"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_texts = [text for _, text in scored[:top_k]]
        return [{"summary": t} for t in top_texts]

    # ==========================================================
    # --- USER PREFERENCES (MongoDB)
    # ==========================================================
    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        prefs = await preferences_collection.find_one({"user_id": user_id})
        return prefs.get("preferences", {}) if prefs else {}

    async def save_preferences(self, user_id: str, new_prefs: dict):
        await preferences_collection.update_one(
            {"user_id": user_id},
            {"$set": {"preferences": new_prefs}},
            upsert=True
        )

    # ==========================================================
    # --- USER ACTIVITY LOG (MongoDB)
    # ==========================================================
    async def append_user_activity(self, user_id: str, activity: Dict[str, Any]):
        """Store user task or activity event."""
        activity_doc = {
            "user_id": user_id,
            "activity": activity,
            "timestamp": datetime.datetime.utcnow(),
        }
        await notes_collection.insert_one(activity_doc)
