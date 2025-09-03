import os
import smtplib
import math
import requests
from datetime import datetime, timedelta
import redis
from email.mime.text import MIMEText
from .celery_app import celery_app
from dotenv import load_dotenv

load_dotenv()

# Redis connection
# Redis connection (use Cloud URL)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


# -------------------- Reminder --------------------
@celery_app.task(name="tasks.set_reminder")
def set_reminder(message: str, minutes: int, user_id="default"):
    trigger_time = datetime.now() + timedelta(minutes=minutes)
    reminder_id = f"reminder:{user_id}:{trigger_time.timestamp()}"
    r.hset(reminder_id, mapping={"time": trigger_time.isoformat(), "message": message})
    r.expireat(reminder_id, trigger_time)
    return f"⏰ Reminder set: '{message}' in {minutes} min"

@celery_app.task(name="tasks.check_reminders")
def check_reminders(user_id="default"):
    keys = r.keys(f"reminder:{user_id}:*")
    now = datetime.now()
    due = []
    for k in keys:
        reminder = r.hgetall(k)
        reminder_time = datetime.fromisoformat(reminder["time"])
        if reminder_time <= now:
            due.append(reminder["message"])
            r.delete(k)
    if due:
        return f"🔔 Reminders: " + ", ".join(due)
    return None

# -------------------- Notes --------------------
@celery_app.task(name="tasks.add_note")
def add_note(note: str, user_id="default"):
    note_id = f"note:{user_id}:{datetime.now().timestamp()}"
    r.set(note_id, note)
    return f"📝 Note saved: {note}"

@celery_app.task(name="tasks.get_notes")
def get_notes(user_id="default"):
    keys = r.keys(f"note:{user_id}:*")
    notes = [r.get(k) for k in keys]
    if not notes:
        return "No notes found."
    return "📒 Notes:\n" + "\n".join(f"- {n}" for n in notes)

# -------------------- Weather --------------------
@celery_app.task(name="tasks.get_weather")
def get_weather(city: str):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    res = requests.get(url).json()
    if res.get("cod") != 200:
        return f"❌ Could not fetch weather for {city}"
    temp = res["main"]["temp"]
    desc = res["weather"][0]["description"]
    return f"🌤️ Weather in {city}: {temp}°C, {desc}"

# -------------------- Web Search --------------------
@celery_app.task(name="tasks.web_search")
def web_search(query: str):
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    res = requests.get(url).json()
    answer = res.get("AbstractText") or res.get("Heading") or "No direct answer found."
    return f"🔍 Search result: {answer}"

# -------------------- Email --------------------
@celery_app.task(name="tasks.send_email")
def send_email(to_email: str, subject: str, body: str):
    from_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.sendmail(from_email, [to_email], msg.as_string())
        return f"📧 Email sent to {to_email}"
    except Exception as e:
        return f"❌ Failed to send email: {e}"

# -------------------- Calculator --------------------
@celery_app.task(name="tasks.calculate")
def calculate(expression: str):
    try:
        result = eval(expression, {"__builtins__": None, "math": math})
        return f"🧮 {expression} = {result}"
    except Exception:
        return "❌ Invalid math expression."
