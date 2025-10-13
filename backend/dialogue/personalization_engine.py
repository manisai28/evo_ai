from typing import Dict, Any
from backend.core.database import users_collection
from backend.memory.memory_manager import MemoryManager


class PersonalizationEngine:
    """Manages user personalization, preferences, and adaptive responses."""

    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.mongo = users_collection

    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Retrieve stored personalization profile for a user."""
        user = await self.mongo.find_one({"_id": user_id})
        if not user:
            return {"tone": "helpful", "formality": "neutral", "language": "en"}
        return user.get(
            "preferences",
            {"tone": "helpful", "formality": "neutral", "language": "en"}
        )

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

    # 🔹 NEW FUNCTION: Adaptive communication style
    async def adapt_communication_style(self, user_id: str, message: str) -> Dict[str, Any]:
        """Adapt response style dynamically based on user preferences in memory."""
        preferences = await self.memory.get_preferences(user_id)

        style_rules = {
            "formality": "casual" if preferences.get("casual_tone") else "professional",
            "humor_level": preferences.get("humor_level", "moderate"),
            "detail_level": preferences.get("prefers_detail", "normal")
        }

        return style_rules
