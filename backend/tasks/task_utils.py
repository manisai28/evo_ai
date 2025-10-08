import importlib
import re
from typing import Dict, Tuple, Any
from backend.core.celery_app import celery_app

# Task mapping
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
}

def detect_task(message: str) -> Tuple[str, Dict]:
    """
    Enhanced task detection with better pattern matching
    """
    message_lower = message.lower().strip()
    
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
    }
    
    # Check retrieval patterns first (show/list commands)
    retrieval_patterns = {
        "notes": [r'show my notes', r'list my notes', r'what did i ask', r'what did you remember'],
        "reminder": [r'show my reminders', r'list my reminders', r'what reminders'],
        "expense": [r'show my expenses', r'list my spending', r'expense summary'],
        "event": [r'show my events', r'list my events', r'upcoming events',r'scheduled events'],
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
        
        # Wait for result with timeout
        return result.get(timeout=10)
        
    except Exception as e:
        print(f"Error executing task {task_type}: {e}")
        return f"I understand you want help, but there was an issue: {str(e)}"