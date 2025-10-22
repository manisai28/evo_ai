import importlib
import re
from typing import Dict, Tuple, Any
from backend.core.celery_app import celery_app

# Task mapping - ADD WHATSAPP HERE
TASK_REGISTRY = {
    "calculator": "backend.tasks.calculator_tasks.execute_calculator_task",
    # "email": "backend.tasks.email_tasks.execute_email_task", 
    "event": "backend.tasks.event_tasks.execute_event_task",
    "expense": "backend.tasks.expense_tasks.execute_expense_task",
    "news": "backend.tasks.news_tasks.execute_news_task",
    "notes": "backend.tasks.notes_tasks.execute_notes_task",
    "reminder": "backend.tasks.reminder_tasks.execute_reminder_task",
    "search": "backend.tasks.search_tasks.execute_search_task",
    "translate": "backend.tasks.translate_tasks.execute_translate_task",
    "weather": "backend.tasks.weather_tasks.execute_weather_task",
    "whatsapp": "backend.tasks.whatsapp_tasks.send_whatsapp_message",
    "music": "backend.tasks.music_tasks.play_music_task",  # NEW
}

def detect_task(message: str) -> Tuple[str, Dict]:
    """
    Enhanced task detection with better pattern matching
    """
    message_lower = message.lower().strip()
    
    print(f"🔍 TASK DETECTION DEBUG: Analyzing message: '{message}'")
    
    # WhatsApp detection - ADD THIS SECTION
    whatsapp_result = detect_whatsapp_task(message_lower)
    if whatsapp_result:
        print(f"✅ WHATSAPP DETECTED: {whatsapp_result}")
        return "whatsapp", whatsapp_result
    else:
        print("❌ No WhatsApp pattern matched")
    
    # More specific keyword-based detection
    task_patterns = {
        "calculator": {
            "patterns": [r'calculat(e|ion)', r'what is \d+', r'\d+\s*[\+\-\*\/]\s*\d+'],
            "exclude": []
        },
        # "email": {
        #     "patterns": [r'send email', r'compose email', r'check (inbox|email)'],
        #     "exclude": []
        # },
        "event": {
            "patterns": [r'schedule', r'create event', r'add event'],
            "exclude": [r'show events', r'list events']
        },
        "expense": {
            "patterns": [r'add expense', r'track \$', r'spent \$'],
            "exclude": [r'show expenses', r'list expenses']
        },
        "news": {
            "patterns": [r'news', r'headlines', r'current events'],
            "exclude": []
        },
        "notes": {
            "patterns": [r'remember to', r'note that', r'write down', r'save this'],
            "exclude": [r'show notes', r'list notes', r'what did i ask']
        },
        "reminder": {
            "patterns": [r'remind me to', r'set reminder for', r'alert me to'],
            "exclude": [r'show reminders', r'list reminders']
        },
        "search": {
            "patterns": [r'search for', r'find information', r'look up'],
            "exclude": []
        },
        "translate": {
            "patterns": [r'translate to', r'how to say in', r'what is .+ in'],
            "exclude": []
        },
        "weather": {
            "patterns": [r'weather in', r'forecast for', r'temperature in'],
            "exclude": []
        },
        "music": {
           "patterns": [r'play music', r'play song', r'play .+ by .+', r'play .+ music'],
           "exclude": []
        },
    }
    
    # Check retrieval patterns first (show/list commands)
    retrieval_patterns = {
        "notes": [r'show my notes', r'list my notes', r'what did i ask', r'what did you remember'],
        "reminder": [r'show my reminders', r'list my reminders', r'what reminders'],
        "expense": [r'show my expenses', r'list my spending', r'expense summary'],
        "event": [r'show my events', r'list my events', r'upcoming events',r'scheduled events'],
        "music": [r'recent music', r'played songs', r'music history'],
    }
    
    # Check for retrieval commands first
    for task_type, patterns in retrieval_patterns.items():
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return f"retrieve_{task_type}", {"query": message, "action": "retrieve"}
    
    # Check for task creation commands
    for task_type, patterns in task_patterns.items():
        # Check if message matches any pattern
        matches_pattern = any(re.search(pattern, message_lower) for pattern in patterns["patterns"])
        
        # Check if message should be excluded
        excluded = any(re.search(exclude, message_lower) for exclude in patterns["exclude"])
        
        if matches_pattern and not excluded:
            return task_type, {"query": message, "action": "create"}
    
    return None, {}

def detect_whatsapp_task(message_lower: str) -> Dict[str, Any]:
    """
    Detect WhatsApp message sending intent - FIXED VERSION
    """
    print(f"🔍 WHATSAPP DETECTION: Checking '{message_lower}'")
    
    # More flexible patterns that match natural language
    patterns = [
        # Immediate messages - more flexible patterns
        (r'send\s+whatsapp\s+(?:message|msg)?\s+to\s+(\+?[\d\s\-\(\)]{10,15})\s*(?:saying|with|:)?\s*(.+)', 'extract_phone_message'),
        (r'whatsapp\s+(\+?[\d\s\-\(\)]{10,15})\s*(.+)', 'extract_phone_message'),
        (r'message\s+(\+?[\d\s\-\(\)]{10,15})\s+(?:on|via)\s+whatsapp\s*(.+)', 'extract_phone_message'),
        (r'send\s+(?:a\s+|an\s+)?(?:message|text)\s+to\s+(\+?[\d\s\-\(\)]{10,15})\s+(?:on|via)\s+whatsapp\s*(.+)', 'extract_phone_message'),
        (r'text\s+(\+?[\d\s\-\(\)]{10,15})\s+on\s+whatsapp\s*(.+)', 'extract_phone_message'),
        
        # Scheduled messages - more flexible
        (r'send\s+whatsapp\s+to\s+(\+?[\d\s\-\(\)]{10,15})\s+in\s+(\d+)\s*(?:minutes?|mins?)\s*(.+)', 'extract_scheduled'),
        (r'whatsapp\s+(\+?[\d\s\-\(\)]{10,15})\s+in\s+(\d+)\s*(?:minutes?|mins?)\s*(.+)', 'extract_scheduled'),
        (r'schedule\s+whatsapp\s+to\s+(\+?[\d\s\-\(\)]{10,15})\s+in\s+(\d+)\s*(?:minutes?|mins?)\s*(.+)', 'extract_scheduled'),
    ]
    
    for pattern, handler in patterns:
        match = re.search(pattern, message_lower)
        print(f"🔍 Pattern '{pattern}': match={match}")
        if match:
            if handler == 'extract_phone_message':
                phone = match.group(1).strip()
                msg_text = match.group(2).strip()
                print(f"✅ EXTRACTED: phone={phone}, message={msg_text}")
                return {
                    "to_number": phone,
                    "message": msg_text,
                    "delay_minutes": 0,
                    "query": f"Send WhatsApp to {phone}: {msg_text}",
                    "action": "create"
                }
            elif handler == 'extract_scheduled':
                phone = match.group(1).strip()
                delay = int(match.group(2))
                msg_text = match.group(3).strip()
                print(f"✅ EXTRACTED SCHEDULED: phone={phone}, delay={delay}, message={msg_text}")
                return {
                    "to_number": phone,
                    "message": msg_text,
                    "delay_minutes": delay,
                    "query": f"Send WhatsApp to {phone} in {delay} minutes: {msg_text}",
                    "action": "create"
                }
    
    print("❌ No WhatsApp patterns matched")
    return None

async def run_task(task_type: str, task_args: Dict) -> Any:
    """
    Execute the appropriate Celery task
    """
    try:
        # Handle retrieval tasks differently
        if task_type.startswith("retrieve_"):
            base_task_type = task_type.replace("retrieve_", "")
            task_path = TASK_REGISTRY[base_task_type]
        else:
            task_path = TASK_REGISTRY[task_type]
        
        # Send task to Celery
        result = celery_app.send_task(task_path, args=[task_args])
        
        # Set longer timeout for WhatsApp (30 seconds)
        timeout = 30 if task_type == "whatsapp" else 10
        
        # Wait for result with appropriate timeout
        return result.get(timeout=timeout)
        
    except Exception as e:
        print(f"Error executing task {task_type}: {e}")
        return f"I understand you want help, but there was an issue: {str(e)}"