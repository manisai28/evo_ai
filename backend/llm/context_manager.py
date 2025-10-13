# backend/llm/context_manager.py
import datetime
from typing import List, Dict, Any, Optional
from backend.memory.memory_manager import MemoryManager
from backend.memory.redis_memory import redis_memory
# from backend.llm.llm_handler import ask_gemini  # <-- Ensure this import is correct

class ContextManager:
    def __init__(self):
        self.memory_manager = MemoryManager()
    
    async def build_context_for_query(self, user_id: str, session_key: str, query: str) -> Dict[str, Any]:
        """
        Build comprehensive context for LLM response generation
        """
        # 1. Recall all relevant memories
        memory_context = await self.memory_manager.recall_context(user_id, query, session_key)
        
        # 2. Get current conversation state
        conversation_history = await redis_memory.get_conversation_history(session_key, limit=8)
        current_state = await redis_memory.get_user_state(user_id) or {}
        
        # 3. Build enhanced context
        enhanced_context = {
            # Memory components
            "memory_summary": memory_context["summary"],
            "user_preferences": memory_context["preferences"],
            "relevant_facts": memory_context["long_term"][:3],  # Top 3 facts
            "semantic_memories": memory_context["semantic"],
            
            # Conversation components
            "recent_messages": conversation_history[-4:],  # Last 4 messages
            "conversation_topic": await self._detect_conversation_topic(conversation_history, query),
            
            # User state
            "user_state": current_state,
            "current_task": current_state.get("current_task"),
            
            # Metadata
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "user_id": user_id,
            "session_id": session_key
        }
        
        # 4. Update working context
        await redis_memory.set_working_context(session_key, {
            "current_topic": enhanced_context["conversation_topic"],
            "last_query": query,
            "timestamp": enhanced_context["timestamp"]
        })
        
        return enhanced_context

    # ==========================================================
    # ENHANCED DYNAMIC TOPIC DETECTION SECTION
    # ==========================================================
    async def _detect_conversation_topic(self, conversation_history: List[Dict], current_query: str) -> str:
        """DYNAMIC topic detection - works for ANY subject"""
        
        if not conversation_history:
            return "new_conversation"
        
        # Combine recent context
        recent_text = " ".join([msg.get('content', '') for msg in conversation_history[-3:]]) + " " + current_query
        recent_text = recent_text.lower()
        
        # Use LLM for dynamic topic detection (or fallback to keyword-based)
        detected_topic = await self._llm_detect_topic(recent_text)
        
        return detected_topic

    async def _llm_detect_topic(self, text: str) -> str:
        """Use LLM to detect ANY topic dynamically"""
        try:
            prompt = f"""
            Analyze this conversation text and identify the MAIN topic being discussed.
            Return ONLY the topic name (1-3 words maximum).

            Conversation: "{text}"

            Topic:"""
            
            # Use your existing Gemini call
            response = await ask_gemini([{"role": "user", "content": prompt}], "system")
            topic = response.get("text", "general").strip().lower()
            
            # Clean up response
            if len(topic) > 30:  # Too long, use fallback
                return self._keyword_fallback_topic(text)
            
            return topic if topic else "general"
            
        except Exception:
            return self._keyword_fallback_topic(text)

    def _keyword_fallback_topic(self, text: str) -> str:
        """Fallback topic detection using broader categories"""
        text_lower = text.lower()
        
        # Broader categories - easily expandable
        category_patterns = {
            "sports": ["cricket", "football", "sports", "game", "match", "player", "team"],
            "technology": ["computer", "phone", "app", "software", "tech", "programming"],
            "food": ["food", "restaurant", "cook", "eat", "meal", "recipe"],
            "travel": ["travel", "trip", "visit", "go to", "vacation", "flight"],
            "work": ["work", "job", "office", "career", "project", "meeting"],
            "entertainment": ["movie", "music", "show", "book", "game", "entertainment"],
            "health": ["health", "exercise", "doctor", "hospital", "fitness", "diet"],
            "shopping": ["buy", "purchase", "shop", "shopping", "store", "price"]
        }
        
        for category, keywords in category_patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "general"

    # ==========================================================
    # CONTEXT UPDATE & STATE MANAGEMENT
    # ==========================================================
    async def update_context_after_response(self, user_id: str, session_key: str, query: str, response: str, context: Dict[str, Any]):
        """
        Update context after generating response
        """
        # 1. Store the interaction in memory
        await self.memory_manager.store_interaction(user_id, session_key, query, response)
        
        # 2. Update conversation history
        await redis_memory.store_conversation_turn(session_key, "user", query)
        await redis_memory.store_conversation_turn(session_key, "assistant", response)
        
        # 3. Extract and update user state
        state_updates = await self._extract_state_updates(query, response, context)
        if state_updates:
            await redis_memory.update_user_state(user_id, state_updates)
        
        # 4. Log the interaction
        await self.memory_manager.append_user_activity(user_id, {
            "type": "conversation",
            "query": query,
            "response": response,
            "context_used": context.get("conversation_topic", "unknown")
        })
    
    async def _extract_state_updates(self, query: str, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract state updates from interaction"""
        updates = {}
        
        # Detect if user is starting a task
        task_keywords = ["calculate", "compute", "find", "show me", "tell me"]
        if any(keyword in query.lower() for keyword in task_keywords):
            updates["current_task"] = query.lower()
        
        # Detect if conversation topic changed significantly
        if "topic_change" in context:
            updates["last_topic_change"] = datetime.datetime.utcnow().isoformat()
        
        return updates
    
    async def get_conversation_summary(self, session_key: str) -> Dict[str, Any]:
        """Get summary of current conversation"""
        history = await redis_memory.get_conversation_history(session_key)
        working_context = await redis_memory.get_working_context(session_key)
        
        return {
            "message_count": len(history),
            "current_topic": working_context.get("current_topic") if working_context else "unknown",
            "last_message_time": history[-1]["timestamp"] if history else None,
            "recent_messages": [{"role": msg["role"], "content": msg["content"][:100]} for msg in history[-3:]]
        }


# ==========================================================
# GLOBAL INSTANCE
# ==========================================================
context_manager = ContextManager()
