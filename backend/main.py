import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.dialogue.dialogue_manager import DialogueManager
from backend.models.schemas import DialogueRequest, DialogueResponse
from backend import auth

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

        # Send plain text
        await ws.send_text(reply)

