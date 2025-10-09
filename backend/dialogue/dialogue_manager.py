# backend/dialogue/dialogue_manager.py
import re
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List

from backend.core.logger import get_logger
# from backend.llm.llm_handler import ask_gemini
from backend.llm.fallback_handler import ask_with_fallback

from backend.memory.memory_manager import MemoryManager
from backend.tasks.task_utils import detect_task, run_task
from backend.dialogue.personalization_engine import PersonalizationEngine
from backend.loggers.personalization_logger import PersonalizationLogger

logger = get_logger(__name__)


class DialogueManager:
    """
    Unified Dialogue Manager:
    - Retrieves context (short-term + long-term + semantic)
    - Detects and executes tasks (Celery-based)
    - Personalizes conversation using user profile/preferences
    - Logs personalization interactions
    - Handles Gemini LLM interaction
    """

    def __init__(self, memory: MemoryManager, personalization: Optional[PersonalizationEngine] = None):
        self.memory = memory
        self.personalization = personalization or PersonalizationEngine(memory)
        self.session_key_template = "session:{user_id}"
        self.logger = PersonalizationLogger()

    async def handle_message(self, user_id: str, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Main dialogue entrypoint."""
        logger.info("Handling message for user=%s session=%s", user_id, session_id)
        timestamp = datetime.utcnow().isoformat()
        session_key = session_id or f"{user_id}:{int(datetime.utcnow().timestamp())}"

        # Step 1: Save user message
        await self._append_conversation(user_id, session_key, "user", message, timestamp)

        # Step 2: Detect and handle task
        try:
            task_type, task_args = detect_task(message)
            if task_type:
                logger.info(f"Detected task: {task_type} for user={user_id}")

                # Run the task (sync or async-safe)
                task_result = await asyncio.get_event_loop().run_in_executor(
                    None, run_task, task_type, {**task_args, "user_id": user_id}
                )

                # ⚠️ Ensure task_result is not a coroutine
                if asyncio.iscoroutine(task_result):
                    task_result = await task_result

                # Store user activity safely
                await self.memory.append_user_activity(
                    user_id,
                    {
                        "type": "task",
                        "task_name": task_type,
                        "result": task_result,  # ✅ now safe
                        "timestamp": timestamp,
                    },
                )

                reply = (
                    task_result.get("reply")
                    if isinstance(task_result, dict)
                    else str(task_result) or f"Executed {task_type} task successfully."
                )

                await self._append_conversation(user_id, session_key, "assistant", reply, timestamp)
                await self.logger.log_interaction(user_id, message, reply, {"task_type": task_type})

                return {"reply": reply, "metadata": {"task": True, "task_name": task_type, "task_result": task_result}}

        except Exception as e:
            logger.exception("⚠️ Task execution failed for user=%s: %s", user_id, str(e))

        # Step 3: Retrieve memory & preferences
        short_context = await self.memory.get_session_conversation(user_id, session_key, limit=10)
        long_context = await self.memory.get_long_term(user_id, limit=10)  # normal long-term
        semantic_context = await self.memory.retrieve_semantic_memory(user_id, message, top_k=5)
        user_profile = await self.personalization.get_profile(user_id)

        # Step 4: Build system prompt from personalization
        system_prompt = self._build_system_prompt(user_profile)
        messages_for_llm = self._assemble_messages(system_prompt, long_context, short_context, semantic_context, message)

        # Step 5: Ask Gemini for response
        try:
            # llm_response = await ask_gemini(messages_for_llm)  # removed user_id argument
            llm_response = await ask_with_fallback(messages_for_llm, user_id=user_id)

            assistant_text = llm_response.get("text") if isinstance(llm_response, dict) else str(llm_response)
        except Exception as e:
            logger.exception("⚠️ Gemini API Error for user=%s: %s", user_id, str(e))
            assistant_text = "⚠️ Sorry, Gemini is temporarily unavailable."

        # Step 6: Personalize final output
        assistant_text = self.personalization.adapt_response(user_id, assistant_text)

        # Step 7: Save assistant response + extracted facts
        await self._append_conversation(user_id, session_key, "assistant", assistant_text, timestamp)
        extracted_facts = self._extract_facts(assistant_text)
        if extracted_facts:
            await self.memory.store_long_term_memory(user_id, extracted_facts)

        # Step 8: Update personalization based on interaction
        await self.personalization.observe_interaction(user_id, message, assistant_text)

        # Step 9: Log the entire interaction
        context_len = len(short_context) + len(long_context) + len(semantic_context)
        await self.logger.log_interaction(user_id, message, assistant_text, {"context_len": context_len})

        return {
            "reply": assistant_text,
            "metadata": {"task": False, "llm_meta": llm_response if isinstance(llm_response, dict) else {}},
        }

    async def _append_conversation(self, user_id: str, session_key: str, role: str, text: str, ts: str):
        """Store conversation message in Redis (short-term)."""
        try:
            await self.memory.append_to_session(session_key, {"role": role, "text": text, "ts": ts})
        except Exception as e:
            logger.warning(f"⚠️ Failed to append to session memory for {user_id}: {e}")

    def _assemble_messages(
        self,
        system_prompt: str,
        long_context: List[Dict],
        short_context: List[Dict],
        semantic_context: List[Dict],
        user_message: str
    ) -> List[Dict]:
        """Build conversation list for Gemini including semantic memory."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Normal long-term memories
        for mem in long_context:
            summary = mem.get("summary") or mem.get("text") or str(mem)
            messages.append({"role": "assistant", "content": f"Memory: {summary}"})

        # Semantic memory
        for sem in semantic_context:
            messages.append({"role": "assistant", "content": f"Relevant fact: {sem['summary']}"})

        # Short-term conversation
        for turn in short_context:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("text", "")})

        # Current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _build_system_prompt(self, user_profile: Dict[str, Any]) -> str:
        """Create system prompt based on personalization settings."""
        tone = user_profile.get("tone", "helpful")
        formality = user_profile.get("formality", "neutral")
        pronouns = user_profile.get("pronouns", "they/them")
        language = user_profile.get("language", "en")

        return (
            f"You are a {tone} assistant. Use {formality} language. Use pronouns: {pronouns}. "
            f"Respond in {language}. Keep responses concise and friendly."
        )

    def _extract_facts(self, text: str) -> List[Dict]:
        """Regex-based fact extraction for semantic memory."""
        facts = []
        fav_match = re.search(r"favorite (?:food|color|movie|hobby) is ([\w\s]+)", text, re.IGNORECASE)
        if fav_match:
            facts.append({
                "type": "preference",
                "key": "favorite",
                "value": fav_match.group(1).strip(),
                "source": "assistant_extraction"
            })

        location_match = re.search(r"I live in ([\w\s]+)", text, re.IGNORECASE)
        if location_match:
            facts.append({
                "type": "preference",
                "key": "location",
                "value": location_match.group(1).strip(),
                "source": "assistant_extraction"
            })

        return facts
