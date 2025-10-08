import datetime
import json
from backend.database import redis_client, users_collection, get_user_preferences
from backend.llm_handler import ask_gemini
from backend.task_utils import detect_task, run_task


class DialogueManager:
    def __init__(self):
        self.redis = redis_client
        self.users = users_collection

    async def get_context(self, user_id: str):
        """Fetch short-term (Redis) + long-term (Mongo) context + preferences."""
        # Short-term memory from Redis
        short_term = await self.redis.get(f"context:{user_id}")
        if short_term:
            if isinstance(short_term, bytes):
                short_term = short_term.decode("utf-8")
        else:
            short_term = ""

        # Long-term memory (MongoDB)
        user_profile = await self.users.find_one({"_id": user_id}) or {}

        # User preferences
        preferences_data = await get_user_preferences(user_id)
        preferences = preferences_data.get("preferences", {}) if preferences_data else {}

        return short_term, user_profile, preferences

    async def save_context(self, user_id: str, context: str):
        """Save dialogue context into Redis (short-term) and MongoDB (long-term)."""
        try:
            # Save to Redis (expires in 5 minutes)
            await self.redis.setex(f"context:{user_id}", 300, context)

            # Save conversation history to MongoDB
            await self.users.update_one(
                {"_id": user_id},
                {
                    "$push": {
                        "conversation_history": {
                            "timestamp": datetime.datetime.utcnow(),
                            "context": context
                        }
                    }
                },
                upsert=True,
            )
        except Exception as e:
            print(f"⚠️ Error saving context: {e}")

    async def handle_message(self, user_id: str, msg: str) -> str:
        """Main dialogue pipeline that handles memory, tasks, and Gemini reasoning."""

        # Step 1: Load short-term + long-term memory
        short_term, user_profile, prefs = await self.get_context(user_id)

        # Step 2: Check if message triggers a Celery task
        try:
            task_type, task_args = detect_task(msg)
            if task_type:
                # ✅ Added user_id to task arguments
                task_info = await run_task(task_type, {
                    **task_args,
                    "user_id": user_id
                })

                # Build context including the task execution
                new_context = f"{short_term} | User: {msg} | Assistant: Executed {task_type} task"
                await self.save_context(user_id, new_context)

                return task_info
        except Exception as e:
            print(f"⚠️ Task execution error: {e}")
            # Continue with normal chat flow even if task fails

        # Step 3: Build personalized prompt for Gemini (non-task messages)
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

        # Step 4: Ask Gemini for response
        try:
            reply = await ask_gemini(prompt)
        except Exception as e:
            return f"⚠️ Gemini API Error: {str(e)}"

        # Step 5: Save updated context
        new_context = f"{short_term} | User: {msg} | Assistant: {reply}"
        await self.save_context(user_id, new_context)

        return reply
