import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.dialogue.dialogue_manager import DialogueManager
from backend.memory.memory_manager import MemoryManager
from backend.dialogue.personalization_engine import PersonalizationEngine
from backend.models.schemas import DialogueRequest, DialogueResponse
from backend import auth
from fastapi import BackgroundTasks
from datetime import datetime

# --- Initialize FastAPI ---
app = FastAPI()

# --- Initialize Core Components ---
memory = MemoryManager()
personalization = PersonalizationEngine(memory)
dm = DialogueManager(memory, personalization)

# --- Enable CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Routes ---
app.include_router(auth.router)

# Store the latest reminder for each user
user_reminders = {}

# --- REST API for Dialogue ---
@app.post("/chat", response_model=DialogueResponse)
async def chat(request: DialogueRequest):
    """REST API for normal chat."""
    result = await dm.handle_message(request.user_id, request.text)
    return DialogueResponse(user_id=request.user_id, response=result["reply"])

# --- WebSocket for Real-time Dialogue ---
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_text()
        try:
            data_json = json.loads(data)
            user_id = data_json.get("user_id", "guest")
            msg = data_json.get("text", "")
        except Exception:
            user_id, msg = "guest", data

        result = await dm.handle_message(user_id, msg)
        await ws.send_text(result["reply"])

@app.get("/notifications/{user_id}")
async def get_notifications(user_id: str):
    """Get unread reminder notifications for a user"""
    from backend.core.database import get_user_notifications_sync
    try:
        notifications = get_user_notifications_sync(user_id)
        
        # Convert ObjectId to string for JSON serialization
        for notification in notifications:
            notification["_id"] = str(notification["_id"])
            notification["created"] = notification["created"].isoformat()
            
        return {"success": True, "notifications": notifications}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/trigger-reminder")
async def trigger_reminder_simple(data: dict):
    """Store reminder for frontend to pick up"""
    user_id = data.get("user_id", "guest")
    reminder_text = data.get("reminder_text", "")
    
    print(f"🎯 DEBUG: /trigger-reminder called for user {user_id}")
    print(f"🎯 DEBUG: Reminder text: {reminder_text}")
    
    # Store reminder with timestamp
    user_reminders[user_id] = {
        "message": f"🔔 REMINDER: {reminder_text}",
        "timestamp": datetime.now().isoformat(),
        "read": False
    }
    
    print(f"✅ Reminder stored for user {user_id}")
    return {"status": "reminder_stored"}

@app.get("/check-reminders/{user_id}")
async def check_reminders_simple(user_id: str):
    """Check if user has unread reminders"""
    print(f"🔍 Checking reminders for user: {user_id}")
    
    if user_id in user_reminders and not user_reminders[user_id]["read"]:
        print(f"✅ Found unread reminder: {user_reminders[user_id]['message']}")
        return {
            "has_reminder": True,
            "message": user_reminders[user_id]["message"],
            "timestamp": user_reminders[user_id]["timestamp"]
        }
    
    print(f"ℹ️ No reminders found for user: {user_id}")
    return {"has_reminder": False}

@app.post("/mark-reminder-read/{user_id}")
async def mark_reminder_read(user_id: str):
    """Mark reminder as read"""
    if user_id in user_reminders:
        user_reminders[user_id]["read"] = True
        print(f"✅ Marked reminder as read for user: {user_id}")
    return {"status": "marked_read"}