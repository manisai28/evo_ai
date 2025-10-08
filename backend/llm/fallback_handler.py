# backend/llm/fallback_handler.py
import os
import aiohttp
import asyncio
from typing import List, Dict, Any
from backend.core.logger import get_logger

logger = get_logger(__name__)

class FallbackLLMHandler:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    async def try_openai(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback to OpenAI if available"""
        if not self.openai_key:
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    headers={"Authorization": f"Bearer {self.openai_key}"},
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        reply = data["choices"][0]["message"]["content"]
                        return {"text": reply, "via": "openai_fallback"}
            return None
        except Exception as e:
            logger.warning(f"OpenAI fallback failed: {e}")
            return None
    
    async def get_local_fallback(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Local rule-based fallback"""
        last_message = messages[-1]["content"].lower() if messages else ""
        
        greetings = ["hello", "hi", "hey", "greetings"]
        if any(greet in last_message for greet in greetings):
            return {"text": "Hello! I'm currently experiencing technical difficulties with my primary AI service. How can I help you today?", "via": "local_fallback"}
        
        return {"text": "I apologize, but I'm currently experiencing technical difficulties. Please try again in a few moments.", "via": "local_fallback"}

# Enhanced main handler with multiple fallbacks
async def ask_gemini_with_fallbacks(messages: List[Dict[str, Any]], user_id: str = None) -> Dict[str, Any]:
    fallback_handler = FallbackLLMHandler()
    
    # 1. Try Gemini HTTP
    gemini_response = await _call_gemini_http(messages)
    if gemini_response["text"] and not gemini_response["text"].startswith("⚠️"):
        return gemini_response
    
    # 2. Try Gemini SDK
    gemini_sdk_response = await _call_gemini_sdk(messages)
    if gemini_sdk_response["text"] and not gemini_sdk_response["text"].startswith("⚠️"):
        return gemini_sdk_response
    
    # 3. Try OpenAI fallback
    openai_response = await fallback_handler.try_openai(messages)
    if openai_response:
        return openai_response
    
    # 4. Final local fallback
    return await fallback_handler.get_local_fallback(messages)