import re
import os
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .tasks import set_reminder, add_note, get_notes, get_weather, web_search, send_email, calculate
from .llm_handler import ask_gemini   # Gemini helper
from . import auth   # ✅ import auth router

app = FastAPI()

# --- Enable CORS so frontend can talk to backend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 👈 change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Auth Routes ---
app.include_router(auth.router)


# --- Task Detection ---
def detect_task(msg: str):
    msg = msg.lower()

    # Reminder
    match = re.match(r"remind me in (\d+) minutes? to (.+)", msg)
    if match:
        return set_reminder.delay(match.group(2), int(match.group(1)))

    # Notes
    if msg.startswith("note "):
        return add_note.delay(msg.replace("note ", ""))
    if msg.startswith("show notes"):
        return get_notes.delay()

    # Weather
    if msg.startswith("weather "):
        city = msg.replace("weather ", "")
        return get_weather.delay(city)

    # Web search
    if msg.startswith("search "):
        query = msg.replace("search ", "")
        return web_search.delay(query)

    # Email
    if msg.startswith("email "):
        match = re.match(r"email (.+?) subject:(.+?) body:(.+)", msg)
        if match:
            return send_email.delay(
                match.group(1).strip(),
                match.group(2).strip(),
                match.group(3).strip()
            )

    # Calculator
    if msg.startswith("calc "):
        expr = msg.replace("calc ", "")
        return calculate.delay(expr)

    return None


# --- WebSocket ---
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        data = await ws.receive_text()

        try:
            data_json = json.loads(data)
            msg = data_json.get("text", "")
        except Exception:
            msg = data  # fallback if plain text

        task = detect_task(msg)
        if task:
            try:
                result = task.get(timeout=30)  # Celery task result
                await ws.send_text(result)
            except Exception as e:
                await ws.send_text(f"⚠️ Task Error: {e}")
        else:
            # Fallback to Gemini
            reply = ask_gemini(msg)
            await ws.send_text(reply)
