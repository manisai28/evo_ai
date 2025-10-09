import os
import aiohttp
import asyncio
import google.generativeai as genai
from typing import List, Dict, Any
from backend.core.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)

# ==========================================================
# --- CURRENT Gemini Models (October 2025) ---
# ==========================================================
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# ✅ CURRENT AVAILABLE MODELS (as of October 2025)
# Gemini 1.0 models (still available)
GEMINI_1_MODELS = [
    "gemini-1.0-pro",
    "gemini-1.0-pro-001",
]

# ✅ Gemini 2.5 models (NEW - Current)
GEMINI_2_MODELS = [
    "gemini-2.0-flash-exp",           # Latest experimental
    "gemini-2.0-flash",               # Current stable
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.5-flash-lite-preview-09-2025",
]

# Try newest models first, then fall back to older ones
ALL_GEMINI_MODELS = GEMINI_2_MODELS + GEMINI_1_MODELS

# Configure SDK
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("✅ Gemini SDK configured successfully")
        
        # Log available models at startup
        async def log_available_models():
            try:
                def list_models_sync():
                    return list(genai.list_models())
                
                models = await asyncio.to_thread(list_models_sync)
                available_models = [model.name for model in models]
                logger.info(f"📋 Available Gemini models: {available_models}")
            except Exception as e:
                logger.warning(f"⚠️ Could not list models at startup: {e}")
        
        # Run in background
        asyncio.create_task(log_available_models())
        
    except Exception as e:
        logger.error(f"❌ Gemini SDK configuration failed: {e}")
else:
    logger.warning("⚠️ GOOGLE_API_KEY not found in environment variables")

# ==========================================================
# --- Model Testing & Discovery ---
# ==========================================================
async def test_gemini_model(model_name: str) -> Dict[str, Any]:
    """Test if a specific Gemini model works"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    
    payload = {
        "contents": [{"parts": [{"text": "Say just 'OK' if you're working."}]}],
        "generationConfig": {
            "maxOutputTokens": 10,
            "temperature": 0.1
        }
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
                        return {
                            "working": True, 
                            "response": text,
                            "model": model_name
                        }
                    else:
                        return {"working": False, "error": "No candidates in response"}
                else:
                    error_msg = data.get("error", {}).get("message", f"HTTP {resp.status}")
                    return {
                        "working": False, 
                        "error": error_msg,
                        "status": resp.status
                    }
                    
    except Exception as e:
        return {"working": False, "error": str(e)}

async def find_working_gemini_model():
    """Find the first working Gemini model"""
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

# ==========================================================
# --- Main Gemini Implementation ---
# ==========================================================
async def ask_gemini(messages: List[Dict[str, Any]], user_id: str = None) -> Dict[str, Any]:
    """Main Gemini request handler with current models"""
    
    # Basic validation
    if not GEMINI_API_KEY:
        error_msg = "❌ GOOGLE_API_KEY missing. Please check your .env file"
        logger.error(error_msg)
        return {"text": error_msg, "raw_response": {}}
    
    if not messages:
        return {"text": "Please enter a message.", "raw_response": {}}
    
    last_message = messages[-1]["content"]
    
    # Try each model in order
    for model in ALL_GEMINI_MODELS:
        logger.info(f"🚀 Trying Gemini model: {model}")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": last_message}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 512,
            }
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
                    
                    if resp.status == 200:
                        if "candidates" in data and data["candidates"]:
                            text = data["candidates"][0]["content"]["parts"][0]["text"]
                            logger.info(f"✅ SUCCESS with model: {model}")
                            return {
                                "text": text, 
                                "raw_response": data, 
                                "model_used": model,
                                "via": "http"
                            }
                        else:
                            logger.warning(f"⚠️ Model {model} returned empty response")
                    
                    # Log specific error
                    error_msg = data.get("error", {}).get("message", f"HTTP {resp.status}")
                    logger.warning(f"❌ Model {model} failed: {error_msg}")
                    
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Model {model} timeout")
            continue
        except Exception as e:
            logger.warning(f"❌ Model {model} error: {str(e)}")
            continue
    
    # If all models failed
    error_text = """❌ All Gemini models failed. 

This is usually because:
1. Your region (India) may not have access to newer Gemini models yet
2. API key may be invalid or restricted
3. Google Cloud project may need enabling of Gemini API

**Recommended solutions:**
- Use OpenAI as primary (most reliable globally)
- Check https://ai.google.dev/ for available models in your region
- Try using a VPN to test if it's region-related
"""
    logger.error(error_text)
    return {
        "text": error_text,
        "raw_response": {},
        "model_used": "none"
    }

# ==========================================================
# --- Health Check & Diagnostics ---
# ==========================================================
async def check_gemini_health():
    """Check Gemini API health with current models"""
    if not GEMINI_API_KEY:
        return {
            "status": "error", 
            "message": "GOOGLE_API_KEY not configured",
            "solution": "Add GOOGLE_API_KEY to your .env file"
        }
    
    # Test with the most likely working model first
    test_model = "gemini-2.0-flash"  # Most widely available
    
    test_result = await test_gemini_model(test_model)
    
    if test_result["working"]:
        return {
            "status": "healthy",
            "message": f"Gemini is working with {test_result['model']}",
            "model": test_result["model"],
            "response_sample": test_result["response"]
        }
    else:
        # Try to find any working model
        working_model = await find_working_gemini_model()
        
        if working_model:
            return {
                "status": "healthy", 
                "message": f"Gemini is working with {working_model}",
                "model": working_model
            }
        else:
            return {
                "status": "error",
                "message": "No Gemini models are working in your region",
                "details": {
                    "tested_models": ALL_GEMINI_MODELS,
                    "last_error": test_result.get("error"),
                    "solution": "Use OpenAI as primary or check region availability"
                }
            }

async def get_gemini_diagnostics():
    """Get detailed diagnostics about Gemini availability"""
    diagnostics = {
        "api_key_configured": bool(GEMINI_API_KEY),
        "tested_models": [],
        "working_models": [],
        "errors": []
    }
    
    if not GEMINI_API_KEY:
        diagnostics["errors"].append("GOOGLE_API_KEY not found")
        return diagnostics
    
    # Test all models
    for model in ALL_GEMINI_MODELS:
        result = await test_gemini_model(model)
        diagnostics["tested_models"].append({
            "model": model,
            "working": result["working"],
            "error": result.get("error"),
            "status": result.get("status")
        })
        
        if result["working"]:
            diagnostics["working_models"].append(model)
    
    return diagnostics