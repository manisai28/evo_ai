# backend/main.py
import re
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# use absolute imports instead of relative
from backend.tasks import set_reminder, add_note, get_notes, get_weather, web_search, send_email, calculate
from backend.llm_handler import ask_gemini
from backend import auth
from backend.dialogue_manager import DialogueManager
from backend.schemas import DialogueRequest, DialogueResponse
from backend.task_utils import detect_task

app = FastAPI()
dm = DialogueManager()

# --- Enable CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth Routes ---
app.include_router(auth.router)





# --- REST API for Dialogue ---
@app.post("/chat", response_model=DialogueResponse)
async def chat(request: DialogueRequest):
    reply = await dm.handle_message(request.user_id, request.text)
    return DialogueResponse(user_id=request.user_id, response=reply)


# --- WebSocket for Dialogue ---
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

        reply = await dm.handle_message(user_id, msg)
        
        # --- CODE CHANGE ---
        # This is the original line that sends a full JSON object. 
        # I have commented it out as requested.
        # await ws.send_json({"user_id": user_id, "response": reply})

        # This is the new line. It sends ONLY the text reply.
        # This will fix the issue on your frontend.
        await ws.send_text(reply)