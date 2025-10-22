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
from backend.routes.whatsapp_routes import router as whatsapp_router
from backend.routes.music_routes import router as music_router
from backend.voice.voice_manager import VoiceManager

# --- Initialize FastAPI ---
app = FastAPI()

# --- Initialize Core Components ---
memory = MemoryManager()
personalization = PersonalizationEngine(memory)
dm = DialogueManager(memory, personalization)
voice_manager = VoiceManager(dm)

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

# Store active WebSocket connections
active_connections = {}

app.include_router(whatsapp_router, prefix="/api/v1", tags=["whatsapp"])

app.include_router(music_router, prefix="/api/v1", tags=["music"])
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
    user_id = "default_user"  # Default user ID
    
    # Store connection
    if user_id not in active_connections:
        active_connections[user_id] = []
    active_connections[user_id].append(ws)
    
    try:
        while True:
            data = await ws.receive_text()
            try:
                data_json = json.loads(data)
                user_id = data_json.get("user_id", "guest")
                msg = data_json.get("text", "")
                
                # Check if it's a WhatsApp status request
                if "whatsapp" in msg.lower() and "status" in msg.lower():
                    # Send WhatsApp status update
                    status_msg = {
                        "type": "whatsapp_status",
                        "message": "📱 Checking WhatsApp status...",
                        "status": "info"
                    }
                    await ws.send_text(json.dumps(status_msg))
                    
            except Exception:
                user_id, msg = "guest", data

            result = await dm.handle_message(user_id, msg)
            await ws.send_text(result["reply"])
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Remove connection when disconnected
        if user_id in active_connections and ws in active_connections[user_id]:
            active_connections[user_id].remove(ws)

# Function to send WhatsApp status to frontend
async def send_whatsapp_status(user_id: str, message: str, status_type: str = "info"):
    """Send WhatsApp status update to frontend via WebSocket"""
    if user_id in active_connections:
        status_msg = {
            "type": "whatsapp_status",
            "message": message,
            "status": status_type,
            "timestamp": datetime.now().isoformat()
        }
        
        for connection in active_connections[user_id]:
            try:
                await connection.send_text(json.dumps(status_msg))
            except Exception as e:
                print(f"Error sending WhatsApp status: {e}")

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

@app.post("/voice/start")
async def start_voice_mode():
    """Start one-time voice interaction"""
    try:
        # Now this is properly async
        result = await voice_manager.start_voice_interaction()
        return {
            "status": "success", 
            "message": "Voice interaction completed",
            "response": result
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Voice mode failed: {str(e)}"
        }