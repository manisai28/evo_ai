# backend/memory/redis_memory.py
import json
import datetime
from typing import List, Dict, Any, Optional
from backend.core.database import redis_client

class RedisMemory:
    def __init__(self):
        self.short_term_prefix = "stm:"
        self.session_prefix = "session:"
        self.user_prefix = "user:"
    
    # ==================== SESSION MANAGEMENT ====================
    async def create_user_session(self, user_id: str, session_id: str) -> str:
        """Create a new session for user"""
        session_key = f"{self.session_prefix}{user_id}:{session_id}"
        await redis_client.hset(session_key, "created_at", datetime.datetime.utcnow().isoformat())
        await redis_client.expire(session_key, 86400)  # 24 hours
        return session_key
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all active sessions for user"""
        pattern = f"{self.session_prefix}{user_id}:*"
        keys = await redis_client.keys(pattern)
        return keys
    
    # ==================== SHORT-TERM MEMORY ====================
    async def store_conversation_turn(self, session_key: str, role: str, content: str, metadata: Dict = None):
        """Store one conversation turn"""
        key = f"{self.short_term_prefix}{session_key}"
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        await redis_client.rpush(key, json.dumps(message))
        await redis_client.ltrim(key, -20, -1)  # Keep last 20 messages
        await redis_client.expire(key, 7200)    # Expire in 2 hours
    
    async def get_conversation_history(self, session_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history"""
        key = f"{self.short_term_prefix}{session_key}"
        data = await redis_client.lrange(key, -limit, -1)
        return [json.loads(item) for item in data] if data else []
    
    async def clear_conversation_history(self, session_key: str):
        """Clear conversation history"""
        key = f"{self.short_term_prefix}{session_key}"
        await redis_client.delete(key)
    
    # ==================== WORKING MEMORY ====================
    async def set_working_context(self, session_key: str, context: Dict[str, Any]):
        """Set current working context (what we're talking about now)"""
        key = f"{self.short_term_prefix}{session_key}:context"
        await redis_client.setex(key, 3600, json.dumps(context))  # 1 hour
    
    async def get_working_context(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Get current working context"""
        key = f"{self.short_term_prefix}{session_key}:context"
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    
    # ==================== TEMPORARY USER STATE ====================
    async def set_user_state(self, user_id: str, state: Dict[str, Any]):
        """Store temporary user state (current task, preferences, etc)"""
        key = f"{self.user_prefix}{user_id}:state"
        await redis_client.setex(key, 1800, json.dumps(state))  # 30 minutes
    
    async def get_user_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get temporary user state"""
        key = f"{self.user_prefix}{user_id}:state"
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    
    async def update_user_state(self, user_id: str, updates: Dict[str, Any]):
        """Update specific fields in user state"""
        current_state = await self.get_user_state(user_id) or {}
        current_state.update(updates)
        await self.set_user_state(user_id, current_state)

# Create global instance
redis_memory = RedisMemory()