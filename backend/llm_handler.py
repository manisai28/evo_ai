import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- Load .env ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("⚠️ No Gemini API key found. Please set GOOGLE_API_KEY or GEMINI_API_KEY in .env")

genai.configure(api_key=api_key)

def ask_gemini(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  # fast & cheap
        response = model.generate_content(prompt)
        return response.text or "⚠️ No response from Gemini"
    except Exception as e:
        return f"⚠️ Gemini API Error: {e}"
