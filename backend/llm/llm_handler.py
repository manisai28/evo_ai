import os
import aiohttp
import asyncio
import google.generativeai as genai
from typing import List, Dict, Any
from backend.core.logger import get_logger
from dotenv import load_dotenv
from backend.llm.context_manager import context_manager  # ✅ Existing import
from backend.memory.proactive_memory import proactive_memory  # ✅ New import
from backend.memory.follow_up_manager import follow_up_manager  # ✅ New import

load_dotenv()
logger = get_logger(__name__)

# ==========================================================
# --- CURRENT Gemini Models (October 2025) ---
# ==========================================================
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

GEMINI_1_MODELS = [
    "gemini-1.0-pro",
    "gemini-1.0-pro-001",
]

GEMINI_2_MODELS = [
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.5-flash-lite-preview-09-2025",
]

ALL_GEMINI_MODELS = GEMINI_2_MODELS + GEMINI_1_MODELS

# Configure Gemini SDK
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("✅ Gemini SDK configured successfully")

        async def log_available_models():
            try:
                def list_models_sync():
                    return list(genai.list_models())
                models = await asyncio.to_thread(list_models_sync)
                available_models = [model.name for model in models]
                logger.info(f"📋 Available Gemini models: {available_models}")
            except Exception as e:
                logger.warning(f"⚠️ Could not list models at startup: {e}")

        asyncio.create_task(log_available_models())

    except Exception as e:
        logger.error(f"❌ Gemini SDK configuration failed: {e}")
else:
    logger.warning("⚠️ GOOGLE_API_KEY not found in environment variables")

# ==========================================================
# --- Gemini Request Handlers ---
# ==========================================================
async def test_gemini_model(model_name: str) -> Dict[str, Any]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": "Say just 'OK' if you're working."}]}],
        "generationConfig": {"maxOutputTokens": 10, "temperature": 0.1}
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                params={"key": GEMINI_API_KEY},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
                if resp.status == 200:
                    if "candidates" in data and data["candidates"]:
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return {"working": True, "response": text, "model": model_name}
                    else:
                        return {"working": False, "error": "No candidates in response"}
                else:
                    return {
                        "working": False,
                        "error": data.get("error", {}).get("message", f"HTTP {resp.status}"),
                        "status": resp.status,
                    }
    except Exception as e:
        return {"working": False, "error": str(e)}

async def find_working_gemini_model():
    logger.info("🔍 Searching for working Gemini models...")
    for model in ALL_GEMINI_MODELS:
        logger.info(f"🧪 Testing: {model}")
        result = await test_gemini_model(model)
        if result["working"]:
            logger.info(f"✅ Found working model: {model}")
            return model
        else:
            logger.warning(f"❌ Model {model} failed: {result.get('error', 'Unknown error')}")
    logger.error("💥 No working Gemini models found!")
    return None

async def ask_gemini(messages: List[Dict[str, Any]], user_id: str = None) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        error_msg = "❌ GOOGLE_API_KEY missing. Please check your .env file"
        logger.error(error_msg)
        return {"text": error_msg, "raw_response": {}}

    if not messages:
        return {"text": "Please enter a message.", "raw_response": {}}

    last_message = messages[-1]["content"]

    for model in ALL_GEMINI_MODELS:
        logger.info(f"🚀 Trying Gemini model: {model}")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": last_message}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512},
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    params={"key": GEMINI_API_KEY},
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200 and "candidates" in data and data["candidates"]:
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        logger.info(f"✅ SUCCESS with model: {model}")
                        return {"text": text, "raw_response": data, "model_used": model, "via": "http"}
        except Exception as e:
            logger.warning(f"❌ Model {model} error: {str(e)}")
            continue

    error_text = """❌ All Gemini models failed. 
Check API key, region access, or use OpenAI as fallback."""
    logger.error(error_text)
    return {"text": error_text, "raw_response": {}, "model_used": "none"}

# ==========================================================
# --- Context-Aware & Proactive Gemini Handler ---
# ==========================================================
async def ask_gemini_with_context(
    messages: List[Dict[str, Any]], user_id: str, session_key: str
) -> Dict[str, Any]:
    """
    Enhanced Gemini handler with:
    1️⃣ Context retention
    2️⃣ Proactive memory
    3️⃣ Follow-up suggestions
    """
    # Get the last user message
    last_user_message = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_message = msg.get("content", "")
            break

    if not last_user_message:
        return {"text": "Please provide a user message", "raw_response": {}}

    try:
        # 1️⃣ BUILD CONTEXT
        context = await context_manager.build_context_for_query(user_id, session_key, last_user_message)

        # 2️⃣ ENHANCE PROMPT
        enhanced_prompt = _build_enhanced_prompt(last_user_message, context)

        # 3️⃣ CALL LLM
        llm_response = await ask_gemini([{"role": "user", "content": enhanced_prompt}], user_id)

        # 4️⃣ GENERATE PROACTIVE SUGGESTIONS
        anticipations = await proactive_memory.anticipate_user_needs(user_id, context)
        follow_ups = await follow_up_manager.generate_follow_ups(user_id, session_key, llm_response["text"])

        # 5️⃣ STORE CONTEXT
        await context_manager.update_context_after_response(
            user_id, session_key, last_user_message, llm_response["text"], context
        )

        # 6️⃣ ENHANCE RESPONSE
        llm_response["proactive_suggestions"] = anticipations
        llm_response["follow_up_questions"] = follow_ups
        llm_response["context_used"] = {
            "memory_summary": context.get("memory_summary"),
            "topic": context.get("conversation_topic"),
            "has_preferences": bool(context.get("user_preferences")),
        }

        return llm_response

    except Exception as e:
        logger.error(f"Context-aware LLM call failed: {e}")
        return await ask_gemini(messages, user_id)

def _build_enhanced_prompt(user_query: str, context: Dict[str, Any]) -> str:
    return f"""
You are a personal AI assistant with memory and context awareness.

CURRENT CONTEXT:
- Recent conversation: {context.get('memory_summary', 'No recent context')}
- User preferences: {context.get('user_preferences', {})}
- Conversation topic: {context.get('conversation_topic', 'general')}

USER'S CURRENT QUERY: {user_query}

INSTRUCTIONS:
1. Use the context above to provide personalized responses
2. Reference previous conversations when relevant
3. Maintain natural conversation flow
4. If user shares personal information, acknowledge it naturally
5. Be helpful and engaging

RESPONSE:
"""

# ==========================================================
# --- Health Check & Diagnostics ---
# ==========================================================
async def check_gemini_health():
    if not GEMINI_API_KEY:
        return {"status": "error", "message": "GOOGLE_API_KEY not configured", "solution": "Add GOOGLE_API_KEY to .env"}

    test_model = "gemini-2.0-flash"
    test_result = await test_gemini_model(test_model)
    if test_result["working"]:
        return {"status": "healthy", "message": f"Gemini works with {test_result['model']}", "model": test_result["model"], "response_sample": test_result["response"]}
    working_model = await find_working_gemini_model()
    if working_model:
        return {"status": "healthy", "message": f"Gemini works with {working_model}", "model": working_model}
    return {"status": "error", "message": "No working Gemini models found"}

async def get_gemini_diagnostics():
    diagnostics = {"api_key_configured": bool(GEMINI_API_KEY), "tested_models": [], "working_models": [], "errors": []}
    if not GEMINI_API_KEY:
        diagnostics["errors"].append("GOOGLE_API_KEY not found")
        return diagnostics
    for model in ALL_GEMINI_MODELS:
        result = await test_gemini_model(model)
        diagnostics["tested_models"].append({
            "model": model,
            "working": result["working"],
            "error": result.get("error"),
            "status": result.get("status"),
        })
        if result["working"]:
            diagnostics["working_models"].append(model)
    return diagnostics
