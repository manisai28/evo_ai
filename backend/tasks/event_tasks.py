from datetime import datetime
import re
from backend.celery_app import celery_app
from backend.database import get_user_events_sync, save_user_event_sync


@celery_app.task
def execute_event_task(task_args):
    """
    Handles event creation and retrieval (sync version for Celery).
    """
    try:
        query = task_args.get('query', '').lower()
        action = task_args.get('action', 'create')
        user_id = task_args.get('user_id', 'default_user')

        # ===========================
        # Retrieve Events
        # ===========================
        if action == "retrieve" or any(word in query for word in ['list', 'show', 'view', 'upcoming']):
            events = get_user_events_sync(user_id)

            if not events:
                return "📅 No events scheduled yet."

            event_list = "\n".join(
                [f"- {e.get('name', 'Unnamed Event')} (scheduled for {e.get('time', 'unknown time')})"
                 for e in events[-10:]]
            )
            return f"📅 Your events:\n{event_list}"

        # ===========================
        # Create New Event
        # ===========================
        else:
            event_name = extract_event_name(query)
            event_time = extract_event_time(query)

            save_user_event_sync(user_id, event_name, event_time)
            return f"✅ Event '{event_name}' scheduled for {event_time}"

    except Exception as e:
        return f"❌ Event task error: {str(e)}"


# ==========================================================
# Event Name Extraction
# ==========================================================
def extract_event_name(query):
    """Extract event name from the query."""
    time_phrases = [
        'tomorrow', 'today', 'friday', 'monday', 'tuesday', 'wednesday',
        'thursday', 'saturday', 'sunday', 'next week', 'this week', 'at', 'on', 'for'
    ]

    patterns = [
        r'schedule\s+(.+?)\s+(?:for|at|on|tomorrow|today|next)',
        r'create event\s+(.+?)\s+(?:for|at|on|tomorrow|today|next)',
        r'add event\s+(.+?)\s+(?:for|at|on|tomorrow|today|next)',
        r'set event\s+(.+?)\s+(?:for|at|on|tomorrow|today|next)',
        r'schedule\s+(.+)',
        r'create event\s+(.+)',
        r'add event:\s*(.+)',
        r'meeting\s+(.+)',
        r'appointment\s+(.+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            event_name = match.group(1).strip()
            event_name = clean_event_name(event_name, time_phrases)
            if event_name:
                return event_name

    words = query.split()
    if 'schedule' in words:
        idx = words.index('schedule')
        if idx + 1 < len(words):
            potential_name = ' '.join(words[idx + 1:])
            return clean_event_name(potential_name, time_phrases)

    if 'meeting' in words:
        return "Team Meeting"
    if 'appointment' in words:
        return "Doctor Appointment"

    return "Meeting"


def clean_event_name(event_name, time_phrases):
    """Remove time or unnecessary words from event name."""
    words = event_name.split()
    cleaned_words = []

    for word in words:
        if word.lower() not in time_phrases:
            cleaned_words.append(word)
        else:
            break

    cleaned_name = ' '.join(cleaned_words).strip()
    cleaned_name = re.sub(r'^(a|an|the)\s+', '', cleaned_name, flags=re.IGNORECASE)
    return cleaned_name if cleaned_name else "Meeting"


# ==========================================================
# Event Time Extraction
# ==========================================================
def extract_event_time(query):
    """Extract event time from the query."""
    time_patterns = [
        r'for\s+(.+)',
        r'at\s+(.+)',
        r'on\s+(.+)',
        r'tomorrow\s*(.+)',
        r'today\s*(.+)',
        r'next\s+(.+)',
        r'this\s+(.+)'
    ]

    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    for pattern in time_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            time_part = match.group(1).strip()
            time_part = re.sub(
                r'schedule|create|add|set|event|meeting|appointment',
                '',
                time_part,
                flags=re.IGNORECASE
            )
            time_part = re.sub(r'\s+', ' ', time_part).strip()
            if time_part:
                return time_part

    for day in days:
        if day in query.lower():
            return day

    if 'tomorrow' in query.lower():
        return "tomorrow"
    if 'today' in query.lower():
        return "today"
    if 'next week' in query.lower():
        return "next week"

    return "soon"
