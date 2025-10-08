from datetime import datetime
import re
from backend.core.celery_app import celery_app
from backend.core.database import get_user_reminders_sync, save_user_reminder_sync

@celery_app.task
def execute_reminder_task(task_args):
    try:
        query = task_args.get('query', '').lower()
        action = task_args.get('action', 'create')
        user_id = task_args.get('user_id', 'default_user')
        
        if action == "retrieve" or any(word in query for word in ['show', 'list']):
            # Get reminders from MongoDB (sync version)
            reminders = get_user_reminders_sync(user_id)
            
            if not reminders:
                return "⏰ No reminders set yet."
            
            reminder_list = "\n".join([f"- {r['text']} (at {r['time']})" for r in reminders])
            return f"⏰ Your reminders:\n{reminder_list}"
            
        else:
            # Save reminder to MongoDB (sync version)
            reminder_text = extract_reminder_text(query)
            reminder_time = extract_reminder_time(query)
            
            save_user_reminder_sync(user_id, reminder_text, reminder_time)
            
            return f"⏰ Reminder set: '{reminder_text}' for {reminder_time}"
            
    except Exception as e:
        return f"❌ Reminder task error: {str(e)}"

def extract_reminder_text(query):
    """Extract reminder text from query"""
    patterns = [
        r'remind me to\s+(.+)',
        r'remind me\s+(.+)',
        r'set reminder for\s+(.+)',
        r'set reminder to\s+(.+)',
        r'alert me to\s+(.+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            text = match.group(1)
            text = re.sub(r'(at|on|tomorrow|today|in)\s+.+', '', text)
            return text.strip()
    
    words = query.split()
    if 'remind' in words:
        remind_index = words.index('remind')
        if remind_index + 1 < len(words):
            return ' '.join(words[remind_index + 1:])
    
    return "Something important"

def extract_reminder_time(query):
    """Extract reminder time from query"""
    time_patterns = [
        r'at\s+(.+)',
        r'on\s+(.+)', 
        r'tomorrow\s*(.+)',
        r'today\s*(.+)',
        r'in\s+(.+)'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, query)
        if match:
            time_part = match.group(1).strip()
            time_part = re.sub(r'remind me to|set reminder|alert me', '', time_part)
            return time_part.strip()
    
    return "later today"