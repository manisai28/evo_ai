# backend/schemas.py

from pydantic import BaseModel
from typing import Optional, Dict

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    username: str

# Dialogue
class DialogueRequest(BaseModel):
    user_id: str
    text: str

class DialogueResponse(BaseModel):
    user_id: str
    response: str

# --- User Preferences (long-term personalization) ---
class UserPreferences(BaseModel):
    tone: Optional[str] = "neutral"     # casual, professional, friendly
    style: Optional[str] = "short"      # short, detailed, medium
    language: Optional[str] = "en"      # en, hi, te, etc.
    nickname: Optional[str] = None      # e.g., "Kruthin"
    topics: Optional[Dict[str, int]] = {}  # frequency map of interests
