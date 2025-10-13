# backend/memory/memory_manager.py
import json
import datetime
from typing import List, Dict, Any, Optional
from backend.core.database import redis_client, preferences_collection, notes_collection, semantic_collection
from bson import ObjectId

# Semantic embeddings
from sentence_transformers import SentenceTransformer
import numpy as np


class MemoryManager:
    def __init__(self):
        self.short_term_prefix = "stm:"
        self.long_term_prefix = "ltm:"
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    # ==========================================================
    # --- UNIFIED MEMORY RECALL (NEW) ---
    # ==========================================================
    async def recall_context(self, user_id: str, current_query: str, session_key: str) -> Dict[str, Any]:
        """
        Unified memory recall - aggregates all memory types
        """
        short_term = await self.get_session_conversation(user_id, session_key)
        long_term = await self.get_long_term(user_id, limit=5)
        semantic = await self.retrieve_semantic_memory(user_id, current_query, top_k=3)
        preferences = await self.get_preferences(user_id)
        
        context_summary = self._build_context_summary(
            short_term, long_term, semantic, preferences, current_query
        )
        
        return {
            "short_term": short_term,
            "long_term": long_term,
            "semantic": semantic,
            "preferences": preferences,
            "summary": context_summary
        }

    def _build_context_summary(self, short_term: List, long_term: List, semantic: List, preferences: Dict, query: str) -> str:
        """Build a natural language summary of the context"""
        summary_parts = []
        
        if short_term:
            recent_msgs = [msg.get('content', '') for msg in short_term[-3:] if msg.get('content')]
            if recent_msgs:
                summary_parts.append(f"Recent conversation: {' '.join(recent_msgs)}")
        
        if long_term:
            facts = [f"{item.get('key', '')}: {item.get('value', '')}" for item in long_term[:3]]
            if facts:
                summary_parts.append(f"Known facts: {', '.join(facts)}")
        
        if preferences:
            prefs_str = ', '.join([f"{k}: {v}" for k, v in list(preferences.items())[:3]])
            if prefs_str:
                summary_parts.append(f"User preferences: {prefs_str}")
        
        if semantic:
            semantic_facts = [item.get('summary', '') for item in semantic[:2]]
            if semantic_facts:
                summary_parts.append(f"Related knowledge: {', '.join(semantic_facts)}")
        
        return " | ".join(summary_parts) if summary_parts else "No previous context"

    # ==========================================================
    # --- MEMORY STORAGE (ENHANCED) ---
    # ==========================================================
    async def store_interaction(self, user_id: str, session_key: str, query: str, response: str):
        """Store complete interaction across all memory types"""
        await self.append_to_session(session_key, {"role": "user", "content": query})
        await self.append_to_session(session_key, {"role": "assistant", "content": response})
        
        # Extract and store important facts
        facts = self._extract_facts_from_interaction(query, response)
        if facts:
            await self.store_long_term_memory(user_id, facts)
        
        await self.store_semantic_memory(user_id, f"User: {query} | Assistant: {response}")
        await self.generate_conversation_summary(user_id, session_key)

    # ==========================================================
    # --- ADVANCED FACT EXTRACTION (NEW) ---
    # ==========================================================
    def _extract_facts_from_interaction(self, query: str, response: str) -> List[Dict[str, Any]]:
        """Generic fact extraction - works for any topic"""
        facts = []
        
        personal_patterns = [
            ("my name is", "name"),
            ("i live in", "location"), 
            ("i am from", "hometown"),
            ("i work as", "occupation"),
            ("i like", "likes"),
            ("i dislike", "dislikes"),
            ("my favorite", "favorite"),
            ("i love", "loves"),
            ("i hate", "dislikes"),
            ("i prefer", "preferences"),
            ("i enjoy", "enjoys"),
            ("i'm interested in", "interests"),
            ("i have", "possessions"),
            ("i want to", "goals"),
            ("i need", "needs")
        ]
        
        query_lower = query.lower()
        
        # Extract direct statements
        for pattern, fact_type in personal_patterns:
            if pattern in query_lower:
                start_idx = query_lower.find(pattern) + len(pattern)
                value = query[start_idx:].split('.')[0].split('?')[0].strip()
                value = value.replace('"', '').replace("'", "").strip()
                if value and len(value) < 100:
                    facts.append({
                        "type": "personal_info", 
                        "key": fact_type,
                        "value": value,
                        "source": "user",
                        "confidence": 0.8
                    })
        
        # Extract entities like names, places, numbers
        entities = self._extract_entities(query)
        for entity_type, entity_value in entities:
            facts.append({
                "type": "mentioned_entity",
                "key": entity_type,
                "value": entity_value,
                "source": "user",
                "confidence": 0.6
            })
        
        return facts

    def _extract_entities(self, text: str) -> List[tuple]:
        """Extract entities like people, places, organizations"""
        entities = []
        words = text.split()
        
        # Capitalized entities
        sentence_starters = ["The", "This", "That", "These", "Those", "I", "You", "We"]
        capitalized = [word for word in words if word.istitle() and len(word) > 2 and word not in sentence_starters]
        
        for entity in capitalized[:5]:
            clean_entity = entity.strip('.,!?;:')
            if len(clean_entity) > 1:
                entities.append(("mentioned_entity", clean_entity))
        
        # Extract numbers (e.g., ages, years)
        if any(word in text.lower() for word in ["year", "age", "old"]):
            import re
            numbers = re.findall(r'\b\d+\b', text)
            for num in numbers[:2]:
                if 1 <= int(num) <= 120:
                    entities.append(("age", num))
        
        return entities

    # ==========================================================
    # --- ENHANCED SHORT-TERM MEMORY ---
    # ==========================================================
    async def append_to_session(self, session_key: str, message: Dict[str, Any]):
        key = f"{self.short_term_prefix}{session_key}"
        message["timestamp"] = datetime.datetime.utcnow().isoformat()
        await redis_client.rpush(key, json.dumps(message))
        await redis_client.ltrim(key, -15, -1)
        await redis_client.expire(key, 7200)

    async def get_session_conversation(self, user_id: str, session_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        key = f"{self.short_term_prefix}{session_key}"
        data = await redis_client.lrange(key, -limit, -1)
        return [json.loads(item) for item in data] if data else []

    # ==========================================================
    # --- EXISTING METHODS ---
    # ==========================================================
    async def clear_short_term(self, session_key: str):
        await redis_client.delete(f"{self.short_term_prefix}{session_key}")

    async def store_long_term_memory(self, user_id: str, facts: List[Dict[str, Any]]):
        for fact in facts:
            doc = {
                "user_id": user_id,
                "type": fact.get("type", "fact"),
                "key": fact.get("key"),
                "value": fact.get("value"),
                "source": fact.get("source", "assistant"),
                "confidence": fact.get("confidence", 0.7),
                "timestamp": datetime.datetime.utcnow(),
                "text": f"{fact.get('key')}: {fact.get('value')}"
            }
            await notes_collection.insert_one(doc)
            await self.store_semantic_memory(user_id, doc["text"])

    async def get_long_term(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = notes_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        notes = await cursor.to_list(length=limit)
        return notes

    async def store_semantic_memory(self, user_id: str, text: str):
        embedding = self.model.encode(text).tolist()
        doc = {
            "user_id": user_id,
            "text": text,
            "embedding": embedding,
            "timestamp": datetime.datetime.utcnow()
        }
        await semantic_collection.insert_one(doc)

    async def retrieve_semantic_memory(self, user_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_vec = self.model.encode(query)
        cursor = semantic_collection.find({"user_id": user_id})
        all_notes = await cursor.to_list(length=100)

        def cosine(a, b):
            a = np.array(a)
            b = np.array(b)
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        scored = [(cosine(note["embedding"], query_vec), note["text"]) for note in all_notes]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"summary": t} for _, t in scored[:top_k]]

    async def get_preferences(self, user_id: str) -> Dict[str, Any]:
        prefs = await preferences_collection.find_one({"user_id": user_id})
        return prefs.get("preferences", {}) if prefs else {}

    async def save_preferences(self, user_id: str, new_prefs: dict):
        await preferences_collection.update_one(
            {"user_id": user_id},
            {"$set": {"preferences": new_prefs}},
            upsert=True
        )

    async def append_user_activity(self, user_id: str, activity: Dict[str, Any]):
        activity_doc = {
            "user_id": user_id,
            "activity": activity,
            "timestamp": datetime.datetime.utcnow(),
        }
        await notes_collection.insert_one(activity_doc)

    # ==========================================================
    # --- NEW: CONVERSATION SUMMARY ---
    # ==========================================================
    async def generate_conversation_summary(self, user_id: str, session_key: str):
        conversation = await self.get_session_conversation(user_id, session_key, limit=20)
        if len(conversation) >= 10:
            summary_text = f"Conversation covered: {', '.join([msg.get('content', '')[:50] for msg in conversation[-5:]])}"
            await self.store_semantic_memory(user_id, f"Conversation summary: {summary_text}")
