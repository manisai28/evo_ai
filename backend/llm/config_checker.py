# backend/llm/config_checker.py
import os
import aiohttp
import asyncio
from backend.core.logger import get_logger

logger = get_logger(__name__)

async def check_gemini_config():
    """Diagnose Gemini API configuration issues"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    issues = []
    
    if not api_key:
        issues.append("❌ GOOGLE_API_KEY not found in environment variables")
    elif not api_key.startswith("AI"):
        issues.append("❌ GOOGLE_API_KEY format appears incorrect")
    
    # Test API connectivity
    if api_key:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
                    timeout=10
                ) as resp:
                    if resp.status == 401:
                        issues.append("❌ Invalid API key")
                    elif resp.status == 403:
                        issues.append("❌ API key doesn't have proper permissions")
                    elif resp.status == 200:
                        issues.append("✅ API configuration is correct")
        except Exception as e:
            issues.append(f"❌ Cannot reach Gemini API: {e}")
    
    return issues

# Run this during startup
async def validate_llm_config():
    issues = await check_gemini_config()
    for issue in issues:
        if issue.startswith("❌"):
            logger.error(issue)
        else:
            logger.info(issue)
    
    return len([i for i in issues if i.startswith("❌")]) == 0