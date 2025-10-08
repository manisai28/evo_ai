from datetime import datetime
from backend.celery_app import celery_app
from backend.database import get_user_notes_sync, save_user_note_sync
import re

@celery_app.task
def execute_notes_task(task_args):
    try:
        query = task_args.get('query', '').lower()
        action = task_args.get('action', 'create')
        user_id = task_args.get('user_id', 'default_user')
        
        if action == "retrieve" or any(word in query for word in ['show', 'list', 'what did']):
            # Get notes from MongoDB (sync version)
            notes = get_user_notes_sync(user_id)
            
            if not notes:
                return "📝 No notes saved yet."
            
            notes_list = "\n".join([f"- {note['content']} ({note['timestamp'].strftime('%m/%d %I:%M %p')})" for note in notes])
            return f"📝 Your notes:\n{notes_list}"
            
        else:
            # Save note to MongoDB (sync version)
            note_content = extract_note_content(query, task_args.get('user_input', ''))
            
            save_user_note_sync(user_id, note_content)
            
            return f"📝 Note saved: '{note_content}'"
            
    except Exception as e:
        return f"❌ Notes task error: {str(e)}"

def extract_note_content(query, user_input):
    """Extract note content from query"""
    patterns = [
        r'remember to\s+(.+)',
        r'remember that\s+(.+)', 
        r'note that\s+(.+)',
        r'write down\s+(.+)',
        r'save this\s+(.+)',
        r'note:\s*(.+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    clean_input = re.sub(r'(remember|note|write down|save this|show|list)', '', query, flags=re.IGNORECASE)
    return clean_input.strip() or user_input