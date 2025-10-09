import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.dialogue.dialogue_manager import DialogueManager
from backend.memory.memory_manager import MemoryManager
from backend.dialogue.personalization_engine import PersonalizationEngine
from backend.models.schemas import DialogueRequest, DialogueResponse
from backend import auth

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


