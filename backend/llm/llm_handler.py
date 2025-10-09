# backend/llm/llm_handler.py
import os
import aiohttp
import asyncio
import google.generativeai as genai
from typing import List, Dict, Any
from backend.core.logger import get_logger
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

load_dotenv()
logger = get_logger(__name__)

# =============================
# Correct Configuration
# =============================
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
# Correct Gemini API endpoints
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1:generateContent"
GEMINI_CHAT_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1:streamGenerateContent"

# Configure SDK properly
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Gemini SDK configured successfully")
    except Exception as e:
        logger.error(f"Gemini SDK configuration failed: {e}")

# =============================
# Correct HTTP Implementation
# =============================
async def _call_gemini_http(messages: List[Dict[str, Any]], model: str = "gemini-1") -> Dict[str, Any]:
    """
    Correct HTTP implementation for Gemini API
    """
    # Convert chat messages to Gemini format
    last_message = messages[-1]["content"] if messages else ""
    
    payload = {
        "contents": [{
            "parts": [{"text": last_message}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500,
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:

                if resp.status == 429:
                    logger.warning("Gemini API quota exceeded")
                    return {"text": "⚠️ API quota exceeded. Please try again later.", "raw_response": {}}
                elif resp.status == 404:
                    logger.error("Gemini API endpoint not found")
                    return {"text": "⚠️ API configuration error.", "raw_response": {}}
                elif resp.status != 200:
                    text = await resp.text()
                    logger.error(f"Gemini API error {resp.status}: {text}")
                    return {"text": "⚠️ Service temporarily unavailable.", "raw_response": {}}

                data = await resp.json()
                if "candidates" in data and len(data["candidates"]) > 0:
                    reply = data["candidates"][0]["content"]["parts"][0]["text"]
                    return {"text": reply, "raw_response": data}
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return {"text": "⚠️ Unexpected response from API.", "raw_response": data}

    except aiohttp.ClientConnectorError as e:
        logger.error(f"Network error: {e}")
        return {"text": "⚠️ Network error. Please check your connection.", "raw_response": {}}
    except asyncio.TimeoutError:
        logger.error("Gemini API request timeout")
        return {"text": "⚠️ Request timeout. Please try again.", "raw_response": {}}
    except Exception as e:
        logger.exception(f"Unexpected error in HTTP call: {e}")
        return {"text": "⚠️ Service temporarily unavailable.", "raw_response": {}}

# =============================
# Improved SDK Implementation
# =============================
async def _call_gemini_sdk(messages: List[Dict[str, Any]], model: str = "gemini-pro") -> Dict[str, Any]:
    """
    Improved SDK implementation with proper error handling
    """
    try:
        # Convert messages to prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-6:]])  # Last 6 messages for context
        
        # Use async thread for SDK call
        def sdk_call():
            model_obj = genai.GenerativeModel(model)
            response = model_obj.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                )
            )
            return response

        response = await asyncio.to_thread(sdk_call)
        
        if response.text:
            return {"text": response.text, "raw_response": {"via": "sdk"}}
        else:
            logger.warning("Gemini SDK returned empty response")
            return {"text": "⚠️ No response generated. Please try again.", "raw_response": {}}

    except ResourceExhausted:
        logger.warning("Gemini API quota exceeded")
        return {"text": "⚠️ API quota exceeded. Please try again later.", "raw_response": {}}
    except Exception as e:
        logger.error(f"Gemini SDK error: {e}")
        return {"text": f"⚠️ Service error: {str(e)}", "raw_response": {}}

# =============================
# Unified Handler with Retry Logic
# =============================
async def ask_gemini(messages: List[Dict[str, Any]], user_id: str = None) -> Dict[str, Any]:
    """
    Main Gemini handler with fallback strategies
    """
    if not GEMINI_API_KEY:
        logger.error("GOOGLE_API_KEY not found")
        return {"text": "❌ API configuration error. Please contact support.", "raw_response": {}}

    # Validate messages
    if not messages or len(messages) == 0:
        return {"text": "Please provide a message to continue.", "raw_response": {}}

    # Try HTTP first with retry
    max_retries = 2
    for attempt in range(max_retries):
        http_response = await _call_gemini_http(messages)
        if http_response["text"] and not http_response["text"].startswith("⚠️"):
            return http_response
        elif attempt < max_retries - 1:
            await asyncio.sleep(1)  # Wait before retry

    # Fallback to SDK
    logger.info("Falling back to SDK implementation")
    sdk_response = await _call_gemini_sdk(messages)
    return sdk_response