# backend/llm/fallback_handler.py
import os
import asyncio
from backend.llm.llm_handler import ask_gemini, check_gemini_health
from backend.core.logger import get_logger

logger = get_logger(__name__)

# Optional secondary APIs
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    AsyncOpenAI = None
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Load keys
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

# ============================
# Local LLaMA Fallback (Ollama)
# ============================
async def ask_local_llama(prompt: str) -> str:
    """Fallback to local LLaMA via Ollama"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama2",  # Use a model that's commonly available
                    "prompt": prompt,
                    "stream": False
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "⚠️ Local model returned empty response.")
                else:
                    return f"⚠️ Local model error: HTTP {resp.status}"
    except aiohttp.ClientConnectorError:
        return "⚠️ Local model unavailable (Ollama not running or wrong port)."
    except asyncio.TimeoutError:
        return "⚠️ Local model timeout."
    except Exception as e:
        logger.error(f"LLaMA fallback failed: {e}")
        return f"⚠️ Local model error: {str(e)}"

# ============================
# OpenAI Fallback
# ============================
async def ask_openai(prompt: str) -> str:
    """Fallback to OpenAI"""
    if not OPENAI_AVAILABLE or not OPENAI_KEY:
        return "⚠️ OpenAI not configured."
    try:
        client = AsyncOpenAI(api_key=OPENAI_KEY)
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # More widely available
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI fallback failed: {e}")
        return f"⚠️ OpenAI service error: {str(e)}"

# ============================
# Anthropic (Claude) Fallback
# ============================
async def ask_claude(prompt: str) -> str:
    """Fallback to Claude"""
    if not ANTHROPIC_AVAILABLE or not ANTHROPIC_KEY:
        return "⚠️ Claude not configured."
    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_KEY)
        message = await client.messages.create(
            model="claude-3-haiku-20240307",  # Cheaper model
            max_tokens=500,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Claude fallback failed: {e}")
        return f"⚠️ Claude service error: {str(e)}"

# ============================
# Unified Fallback Layer
# ============================
async def ask_with_fallback(messages, user_id=None):
    """
    Main LLM handler with fallback chain
    """
    if not messages:
        return {"text": "Please enter a message.", "raw_response": {}}
    
    prompt = messages[-1]["content"]

    # 1. Check Gemini health first
    gemini_health = await check_gemini_health()
    if gemini_health["status"] == "healthy":
        try:
            gemini_response = await ask_gemini(messages, user_id)
            if (gemini_response and 
                gemini_response.get("text") and 
                not gemini_response["text"].startswith("⚠️") and
                not gemini_response["text"].startswith("❌")):
                return gemini_response
        except Exception as e:
            logger.error(f"Gemini failure: {e}")
    
    logger.warning("Gemini failed. Trying OpenAI...")

    # 2. Try OpenAI
    try:
        openai_text = await ask_openai(prompt)
        if openai_text and not openai_text.startswith("⚠️"):
            return {"text": openai_text, "raw_response": {"via": "openai"}}
    except Exception as e:
        logger.error(f"OpenAI fallback error: {e}")

    logger.warning("OpenAI failed. Trying Claude...")

    # 3. Try Claude
    try:
        claude_text = await ask_claude(prompt)
        if claude_text and not claude_text.startswith("⚠️"):
            return {"text": claude_text, "raw_response": {"via": "claude"}}
    except Exception as e:
        logger.error(f"Claude fallback error: {e}")

    logger.warning("Claude failed. Trying LLaMA...")

    # 4. Final fallback to local LLaMA
    try:
        local_text = await ask_local_llama(prompt)
        return {"text": local_text, "raw_response": {"via": "local"}}
    except Exception as e:
        logger.error(f"All fallbacks failed: {e}")
        return {"text": "⚠️ All AI services are currently unavailable. Please try again later.", "raw_response": {"via": "error"}}

# ============================
# Health Check Endpoint
# ============================
async def get_llm_health():
    """Get health status of all LLM services"""
    health_info = {
        "gemini": await check_gemini_health(),
        "openai": {"status": "configured" if OPENAI_KEY else "not_configured"},
        "claude": {"status": "configured" if ANTHROPIC_KEY else "not_configured"},
        "local_llama": {"status": "unknown"}
    }
    
    # Test local llama
    try:
        test_response = await ask_local_llama("Hello")
        health_info["local_llama"]["status"] = "healthy" if not test_response.startswith("⚠️") else "unavailable"
    except:
        health_info["local_llama"]["status"] = "unavailable"
    
    return health_info