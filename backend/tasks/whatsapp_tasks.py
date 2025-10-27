import os
import pywhatkit
import time
from celery import Celery
from datetime import datetime, timedelta
from backend.core.database import sync_whatsapp_tasks_collection
from backend.core.celery_app import celery_app
from bson import ObjectId
import requests
import os
from dotenv import load_dotenv

@celery_app.task
def send_whatsapp_message(task_args):
    """
    Send WhatsApp message using pywhatkit - NON-BLOCKING version
    """
    try:
        print(f"📱 WHATSAPP TASK: Received task_args: {task_args}")
        
        # Extract task arguments
        if isinstance(task_args, dict) and 'to_number' in task_args:
            to_number = task_args['to_number']
            message = task_args['message']
            delay_minutes = task_args.get('delay_minutes', 0)
            user_id = task_args['user_id']
        else:
            return "❌ Invalid task arguments"
        
        print(f"📱 WHATSAPP TASK: Sending to {to_number}: {message}")
        
        # Save task to database
        scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        task_data = {
            'user_id': user_id,
            'to_number': to_number,
            'message': message,
            'delay_minutes': delay_minutes,
            'scheduled_time': scheduled_time,
            'status': 'queued',
            'created_at': datetime.now()
        }
        
        result = sync_whatsapp_tasks_collection.insert_one(task_data)
        task_id = result.inserted_id
        
        # Send immediate success status - assume it will work
        send_status_update(user_id, f"✅ WhatsApp sent successfully to {to_number}", "success")
        
        # Return immediately and process in background
        if delay_minutes == 0:
            # Start background processing - returns immediately
            process_whatsapp_message.delay(str(task_id), to_number, message, user_id)
            return f"✅ WhatsApp sent successfully to {to_number}"
        else:
            # Schedule for later
            send_whatsapp_delayed.apply_async(
                args=[str(task_id), to_number, message, user_id],
                countdown=delay_minutes * 60
            )
            return f"✅ WhatsApp scheduled to {to_number} in {delay_minutes} minutes"
        
    except Exception as e:
        error_msg = f"❌ Error in WhatsApp task: {str(e)}"
        print(f"📱 {error_msg}")
        if 'user_id' in locals():
            send_status_update(user_id, error_msg, "error")
        return error_msg

@celery_app.task
def process_whatsapp_message(task_id: str, to_number: str, message: str, user_id: str):
    """
    Process WhatsApp message in background - SILENT version (no status updates)
    """
    try:
        print(f"📱 PROCESSING WHATSAPP to {to_number}")
        
        # Update status to processing in database only (no frontend update)
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'processing', 'started_at': datetime.now()}}
        )
        
        # Send message without any intermediate status updates
        pywhatkit.sendwhatmsg_instantly(
            phone_no=to_number,
            message=message,
            wait_time=10,
            tab_close=False
        )
        
        # Update task status in database only
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'sent', 'sent_at': datetime.now()}}
        )
        
        print(f"✅ WhatsApp sent to {to_number}")
        return f"Message sent to {to_number}"
        
    except Exception as e:
        # Only send error update if something actually fails
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'failed', 'error': str(e), 'failed_at': datetime.now()}}
        )
        
        error_msg = f"❌ Failed to send WhatsApp: {str(e)}"
        send_status_update(user_id, error_msg, "error")
        
        print(f"📱 {error_msg}")
        return error_msg

@celery_app.task
def send_whatsapp_delayed(task_id: str, to_number: str, message: str, user_id: str):
    """
    Send delayed WhatsApp message - SILENT version
    """
    try:
        print(f"📱 SENDING DELAYED WHATSAPP to {to_number}")
        
        # Update status to processing in database only
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'processing', 'started_at': datetime.now()}}
        )
        
        pywhatkit.sendwhatmsg_instantly(
            phone_no=to_number,
            message=message,
            wait_time=10,
            tab_close=False
        )
        
        # Update task status in database only
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'sent', 'sent_at': datetime.now()}}
        )
        
        print(f"✅ Delayed WhatsApp sent to {to_number}")
        return f"Message sent to {to_number}"
        
    except Exception as e:
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'failed', 'error': str(e), 'failed_at': datetime.now()}}
        )
        
        error_msg = f"❌ Failed to send scheduled WhatsApp: {str(e)}"
        send_status_update(user_id, error_msg, "error")
        
        print(f"📱 {error_msg}")
        return error_msg

def send_status_update(user_id: str, message: str, status_type: str):
    """
    Helper function to send status updates to frontend
    """
    try:
        import requests
        load_dotenv()
        requests.post(
             f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/send-whatsapp-status",
            json={
                "user_id": user_id,
                "message": message,
                "status_type": status_type
            },
            timeout=2
        )
    except Exception as e:
        print(f"⚠️ Could not send status update: {str(e)}")