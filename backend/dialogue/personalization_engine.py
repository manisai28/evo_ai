from typing import Dict, Any
from backend.core.database import users_collection


class PersonalizationEngine:
    """Manages user personalization, preferences, and adaptive responses."""

    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.mongo = users_collection

    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Retrieve stored personalization profile for a user."""
        user = await self.mongo.find_one({"_id": user_id})
        if not user:
            return {"tone": "helpful", "formality": "neutral", "language": "en"}
        return user.get("preferences", {"tone": "helpful", "formality": "neutral", "language": "en"})

    def adapt_response(self, user_id: str, text: str) -> str:
        """Simple tone adaptation."""
        # In the future, tone could modify punctuation, emojis, etc.
        return text.strip()

    async def observe_interaction(self, user_id: str, user_msg: str, bot_reply: str):
        """Learn from each interaction (placeholder)."""
        # For now, we just store message pairs
        await self.mongo.update_one(
            {"_id": user_id},
            {"$push": {"interactions": {"user": user_msg, "assistant": bot_reply}}},
            upsert=True,
        )
