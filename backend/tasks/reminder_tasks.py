from datetime import datetime, timedelta
import re
from backend.core.celery_app import celery_app
from backend.core.database import (
    get_user_reminders_sync, 
    save_user_reminder_sync, 
    delete_user_reminder_sync, 
    mark_reminder_triggered_sync,
    get_pending_reminders_sync,
    update_reminder_celery_task_sync,
    save_user_notification_sync
)

@celery_app.task
def execute_reminder_task(task_args):
    """
    Main reminder task - Handles both creating and listing reminders
    """
    try:
        # Handle task arguments
        if isinstance(task_args, dict):
            query = task_args.get('query', '').lower()
            action = task_args.get('action', 'create')
            user_id = task_args.get('user_id', 'default_user')
        else:
            query = str(task_args).lower() if task_args else ''
            action = 'create'
            user_id = 'default_user'
        
        print(f"🔧 DEBUG: Received task_args: {task_args}")
        print(f"🔧 DEBUG: Parsed - query: '{query}', action: '{action}', user_id: '{user_id}'")
        
        # 🆕 NEW: Check if this is a reminder trigger (not a user command)
        if "reminder triggered:" in query:
            reminder_text = query.replace("reminder triggered:", "").strip()
            return f"🔔 REMINDER: {reminder_text}"
             
        if action == "retrieve" or any(word in query for word in ['show', 'list', 'view']):
            # Get reminders from MongoDB
            reminders = get_user_reminders_sync(user_id)
            
            if not reminders:
                return "⏰ No reminders set yet."
            
            # Filter only pending reminders for display
            pending_reminders = [r for r in reminders if not r.get('is_triggered', False)]
            
            if not pending_reminders:
                return "⏰ No active reminders."
            
            reminder_list = "\n".join([
                f"- {r['text']} (scheduled for {r['scheduled_time'].strftime('%Y-%m-%d %H:%M')})"
                for r in pending_reminders
            ])
            return f"⏰ Your active reminders:\n{reminder_list}"
            
        else:
            # Create new reminder - PRIMARY SYSTEM: Celery ETA
            reminder_text = extract_reminder_text(query)
            reminder_time_str = extract_reminder_time(query)
            
            print(f"🔧 DEBUG: Extracted text: '{reminder_text}'")
            print(f"🔧 DEBUG: Extracted time string: '{reminder_time_str}'")
            
            # Parse the time and calculate exact trigger datetime
            reminder_datetime = parse_reminder_time(reminder_time_str)
            
            print(f"🔧 DEBUG: Final scheduled time: {reminder_datetime}")
            
            # Save to database first (PERSISTENT STORAGE)
            reminder_id = save_user_reminder_sync(
                user_id=user_id,
                text=reminder_text,
                time=reminder_time_str,
                scheduled_time=reminder_datetime
            )
            
            # PRIMARY SYSTEM: Schedule with Celery ETA for exact timing
            scheduled_task = schedule_reminder_with_eta(
                user_id=user_id,
                reminder_id=reminder_id,
                reminder_text=reminder_text,
                reminder_datetime=reminder_datetime
            )
            
            # Store Celery task ID in database for tracking
            if scheduled_task:
                update_reminder_celery_task_sync(reminder_id, scheduled_task.id)
            
            return f"⏰ Reminder set: '{reminder_text}' for {reminder_datetime.strftime('%Y-%m-%d %H:%M')}"
            
    except Exception as e:
        return f"❌ Reminder task error: {str(e)}"

@celery_app.task
def trigger_reminder(user_id, reminder_text, reminder_id):
    """
    Task that actually triggers the reminder notification
    """
    try:
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"🔔 REMINDER TRIGGERED at {current_time} for user {user_id}: {reminder_text}")
        
        # Mark as triggered in database to prevent duplicates
        mark_reminder_triggered_sync(reminder_id)
        
        # Store reminder via HTTP endpoint (NOT DialogueManager)
        import requests
        try:
            response = requests.post(
                "http://localhost:8000/trigger-reminder",
                json={
                    "user_id": user_id,
                    "reminder_text": reminder_text
                },
                timeout=2
            )
            print(f"✅ Reminder stored via HTTP - Status: {response.status_code}")
        except Exception as req_error:
            print(f"❌ HTTP request failed: {req_error}")
        
        return f"🔔 REMINDER: {reminder_text}"
        
    except Exception as e:
        print(f"❌ Error triggering reminder: {e}")
        return f"Error triggering reminder: {e}"
    

def schedule_reminder_with_eta(user_id, reminder_id, reminder_text, reminder_datetime):
    """
    PRIMARY SYSTEM: Schedule reminder using Celery countdown for exact timing
    """
    try:
        now = datetime.now()
        
        # Calculate seconds until reminder time
        delay_seconds = (reminder_datetime - now).total_seconds()
        
        print(f"🕒 DEBUG: Current time: {now}")
        print(f"🕒 DEBUG: Reminder time: {reminder_datetime}")
        print(f"🕒 DEBUG: Delay seconds: {delay_seconds}")
        
        # Only schedule if the time is in the future
        if delay_seconds > 0:
            # Use countdown instead of ETA (better Windows compatibility)
            scheduled_task = trigger_reminder.apply_async(
                args=[user_id, reminder_text, reminder_id],
                countdown=delay_seconds  # Seconds until execution
            )
            
            print(f"📅 PRIMARY SYSTEM: Reminder scheduled with countdown for {delay_seconds:.0f} seconds")
            print(f"   Will trigger at: {reminder_datetime}")
            print(f"   Task ID: {scheduled_task.id}")
            return scheduled_task
        else:
            # If time is in the past, trigger immediately
            print("⚡ Reminder time is in past, triggering immediately")
            trigger_reminder.delay(user_id, reminder_text, reminder_id)
            return None
            
    except Exception as e:
        print(f"❌ Error scheduling reminder: {e}")
        # Even if scheduling fails, reminder is in database and backup system will catch it
        return None

@celery_app.task
def check_missed_reminders():
    """
    BACKUP SYSTEM: Periodic check for missed reminders
    Runs every 10 minutes to catch reminders that Celery ETA might have missed
    (e.g., due to system restart, Celery worker crash, etc.)
    """
    try:
        print("🔍 BACKUP SYSTEM: Checking for missed reminders...")
        
        # Find reminders that should have triggered but haven't
        pending_reminders = get_pending_reminders_sync()
        
        triggered_count = 0
        for reminder in pending_reminders:
            # Check if reminder is past its scheduled time
            if reminder['scheduled_time'] <= datetime.now():
                print(f"🔔 BACKUP: Triggering missed reminder: {reminder['text']}")
                
                # Trigger the reminder
                trigger_reminder.delay(
                    reminder['user_id'],
                    reminder['text'],
                    str(reminder['_id'])
                )
                triggered_count += 1
        
        result_msg = f"✅ Backup check complete. Triggered {triggered_count} missed reminders."
        print(result_msg)
        return result_msg
        
    except Exception as e:
        error_msg = f"❌ Error in backup reminder check: {e}"
        print(error_msg)
        return error_msg

# Natural Language Processing Functions
def extract_reminder_text(query):
    """Extract reminder text from user query"""
    patterns = [
        r'remind me to\s+(.+)',
        r'remind me\s+(.+)',
        r'set reminder for\s+(.+)',
        r'set reminder to\s+(.+)',
        r'alert me to\s+(.+)',
        r'reminder for\s+(.+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            text = match.group(1)
            # Remove time-related phrases to get clean text
            text = re.sub(r'\b(at|on|tomorrow|today|in|next|this)\b\s+.+', '', text, flags=re.IGNORECASE)
            return text.strip()
    
    # Fallback: extract words after "remind" or "reminder"
    words = query.split()
    if 'remind' in words:
        remind_index = words.index('remind')
        if remind_index + 1 < len(words):
            return ' '.join(words[remind_index + 1:])
    
    return "Something important"

def extract_reminder_time(query):
    """Extract reminder time string from user query"""
    print(f"🕒 DEBUG: Extracting time from: '{query}'")
    
    # Handle "at 19:35" format more precisely
    time_match = re.search(r'at\s+(\d{1,2}:\d{2})', query, re.IGNORECASE)
    if time_match:
        time_part = time_match.group(1).strip()
        print(f"🕒 DEBUG: Found 'at' time: '{time_part}'")
        return f"at {time_part}"
    
    # Handle "in X minutes/hours"
    time_match = re.search(r'in\s+(\d+)\s*(minute|hour|day|week)s?', query, re.IGNORECASE)
    if time_match:
        amount = time_match.group(1)
        unit = time_match.group(2)
        print(f"🕒 DEBUG: Found 'in' time: {amount} {unit}s")
        return f"in {amount} {unit}s"
    
    # Handle "tomorrow"
    if 'tomorrow' in query.lower():
        time_match = re.search(r'tomorrow\s*(at\s+\d{1,2}:\d{2})?', query, re.IGNORECASE)
        if time_match and time_match.group(1):
            time_part = time_match.group(1).replace('at', '').strip()
            print(f"🕒 DEBUG: Found tomorrow at: '{time_part}'")
            return f"at {time_part}"
        else:
            print("🕒 DEBUG: Found tomorrow without specific time")
            return "tomorrow"
    
    # Handle "today at"
    time_match = re.search(r'today\s+at\s+(\d{1,2}:\d{2})', query, re.IGNORECASE)
    if time_match:
        time_part = time_match.group(1).strip()
        print(f"🕒 DEBUG: Found today at: '{time_part}'")
        return f"at {time_part}"
    
    print(f"🕒 DEBUG: No time pattern matched, using default 'in 1 hour'")
    return "in 1 hour"  # Default fallback

def parse_reminder_time(time_str):
    """Parse natural language time into exact datetime object"""
    time_str = time_str.lower().strip()
    now = datetime.now()
    
    print(f"🕒 DEBUG: Parsing time string: '{time_str}'")
    print(f"🕒 DEBUG: Current time: {now}")
    
    # Handle "at" times FIRST (most common case)
    if time_str.startswith('at '):
        time_part = time_str[3:].strip()  # Remove "at " prefix
        print(f"🕒 DEBUG: Processing 'at' time: '{time_part}'")
        return combine_date_time(now.date(), time_part)
    
    # Handle "in X minutes/hours/days"
    time_match = re.search(r'in\s+(\d+)\s*(minute|hour|day|week)s?', time_str)
    if time_match:
        amount = int(time_match.group(1))
        unit = time_match.group(2)
        print(f"🕒 DEBUG: Found 'in' format: {amount} {unit}s")
        
        if unit == 'minute':
            return now + timedelta(minutes=amount)
        elif unit == 'hour':
            return now + timedelta(hours=amount)
        elif unit == 'day':
            return now + timedelta(days=amount)
        elif unit == 'week':
            return now + timedelta(weeks=amount)
    
    # Handle "tomorrow"
    if time_str == 'tomorrow':
        tomorrow = now + timedelta(days=1)
        print("🕒 DEBUG: Found 'tomorrow', using default 9 AM")
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    
    print(f"🕒 DEBUG: No specific time pattern found, defaulting to 1 hour from now")
    # Default: 1 hour from now
    return now + timedelta(hours=1)

def combine_date_time(date_obj, time_str):
    """Combine date object with time string to create datetime"""
    try:
        time_str = time_str.strip()
        print(f"🕒 DEBUG: Combining date {date_obj} with time '{time_str}'")
        
        # Handle 12-hour format with AM/PM
        if 'pm' in time_str.lower():
            time_obj = datetime.strptime(time_str, '%I:%M %p').time()
        elif 'am' in time_str.lower():
            time_obj = datetime.strptime(time_str, '%I:%M %p').time()
        else:
            # Handle 24-hour format
            if ':' in time_str:
                time_obj = datetime.strptime(time_str, '%H:%M').time()
            else:
                # Default time if not specified
                time_obj = datetime.strptime('09:00', '%H:%M').time()
        
        result = datetime.combine(date_obj, time_obj)
        print(f"🕒 DEBUG: Combined result: {result}")
        return result
        
    except ValueError as e:
        print(f"🕒 DEBUG: Error parsing time '{time_str}': {e}")
        # Fallback to current time + 1 hour
        fallback = datetime.now() + timedelta(hours=1)
        print(f"🕒 DEBUG: Using fallback: {fallback}")
        return fallback

def get_days_until_next_weekday(target_day):
    """Calculate days until next occurrence of a weekday"""
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    target_index = days.index(target_day.lower())
    current_index = datetime.now().weekday()
    
    days_ahead = target_index - current_index
    if days_ahead <= 0:
        days_ahead += 7
    
    return days_ahead