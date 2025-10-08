from backend.core.celery_app import celery_app

@celery_app.task
def execute_email_task(task_args):
    try:
        query = task_args.get('query', '').lower()
        
        if 'send' in query and 'email' in query:
            # Extract email details
            recipient = extract_recipient(query)
            subject = extract_subject(query)
            
            return f"📧 Email ready to send to: {recipient}\nSubject: {subject}\n\nI can help you compose emails. This would integrate with your email service."
            
        elif 'check' in query and 'email' in query:
            return "📬 You have 3 new emails. This would show your actual inbox when connected to an email service."
            
        else:
            return "📧 I can help you with emails. You can ask me to send emails or check your inbox."
            
    except Exception as e:
        return f"📧 Email task error: {str(e)}"

def extract_recipient(query):
    """Extract recipient from email query"""
    import re
    patterns = [
        r'to\s+(\S+@\S+\.\S+)',
        r'email\s+(\S+@\S+\.\S+)',
        r'send\s+.*?to\s+([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return match.group(1)
    
    return "recipient@example.com"

def extract_subject(query):
    """Extract subject from email query"""
    import re
    subject_match = re.search(r'about\s+(.+)', query)
    if subject_match:
        return subject_match.group(1)
    
    return "Hello"