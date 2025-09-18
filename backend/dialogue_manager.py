# backend/dialogue_manager.py

from backend.database import redis_client, users_collection, get_user_preferences
from backend.llm_handler import ask_gemini
from backend.task_utils import detect_task


class DialogueManager:
    def __init__(self):
        self.redis = redis_client
        self.users = users_collection

    async def get_context(self, user_id: str):
        """Fetch short-term (Redis) + long-term (Mongo) context + preferences."""
        short_term = await self.redis.get(f"context:{user_id}")
        user_profile = await self.users.find_one({"_id": user_id}) or {}
        preferences = await get_user_preferences(user_id)
        return short_term or "", user_profile, preferences.get("preferences", {})

    async def save_context(self, user_id: str, context: str):
        """Save dialogue context into Redis (short-term)."""
        await self.redis.setex(f"context:{user_id}", 300, context)  # expire in 5 min

    async def handle_message(self, user_id: str, msg: str) -> str:
        """Main dialogue pipeline."""
        # Step 1: Load memory
        short_term, user_profile, prefs = await self.get_context(user_id)

        # Step 2: Task detection
        task = detect_task(msg)
        if task:
            try:
                return task.get(timeout=30)  # sync celery
            except Exception as e:
                return f"⚠️ Task Error: {e}"

        # Step 3: Build contextual prompt
        profile_str = f"""
User Preferences:
- Tone: {prefs.get('tone', 'neutral')}
- Style: {prefs.get('style', 'short')}
- Language: {prefs.get('language', 'en')}
- Nickname: {prefs.get('nickname', 'Friend')}
- Topics: {prefs.get('topics', {})}
"""

        prompt = f"""
Conversation so far: {short_term}

{profile_str}

User: {msg}
Assistant:"""

        # Step 4: Query Gemini
        reply = ask_gemini(prompt)

        # Step 5: Save updated context
        new_context = f"{short_term} | User: {msg} | Assistant: {reply}"
        await self.save_context(user_id, new_context)

        return reply
