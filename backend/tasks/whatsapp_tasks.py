import os
import pywhatkit
from celery import Celery
from datetime import datetime, timedelta
from backend.core.database import sync_whatsapp_tasks_collection
from backend.core.celery_app import celery_app
from bson import ObjectId

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
            user_id = task_args.get('user_id', 'default_user')
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
            'status': 'processing',
            'created_at': datetime.now()
        }
        
        result = sync_whatsapp_tasks_collection.insert_one(task_data)
        task_id = result.inserted_id
        
        # Return immediately and process in background
        if delay_minutes == 0:
            # Start background processing - returns immediately
            process_whatsapp_message.delay(str(task_id), to_number, message)
            return f"⏳ Sending WhatsApp to {to_number}..."
        else:
            # Schedule for later
            send_whatsapp_delayed.apply_async(
                args=[str(task_id), to_number, message],
                countdown=delay_minutes * 60
            )
            return f"✅ WhatsApp scheduled to {to_number} in {delay_minutes} minutes"
        
    except Exception as e:
        error_msg = f"❌ Error in WhatsApp task: {str(e)}"
        print(f"📱 {error_msg}")
        return error_msg

@celery_app.task
def process_whatsapp_message(task_id: str, to_number: str, message: str):
    """
    Process WhatsApp message in background (no timeout issues)
    """
    try:
        print(f"📱 PROCESSING WHATSAPP to {to_number}")
        
        # Send status update via HTTP to main.py
        import requests
        try:
            requests.post("http://localhost:8000/send-whatsapp-status", json={
                "user_id": "default_user",
                "message": f"⏳ Sending WhatsApp to {to_number}...",
                "status_type": "info"
            })
        except:
            pass
        
        pywhatkit.sendwhatmsg_instantly(
            phone_no=to_number,
            message=message,
            wait_time=15,
            tab_close=True
        )
        
        # Update task status
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'sent', 'sent_at': datetime.now()}}
        )
        
        # Send success status
        try:
            requests.post("http://localhost:8000/send-whatsapp-status", json={
                "user_id": "default_user", 
                "message": f"✅ WhatsApp successfully sent to {to_number}",
                "status_type": "success"
            })
        except:
            pass
        
        print(f"✅ WhatsApp sent to {to_number}")
        return f"Message sent to {to_number}"
        
    except Exception as e:
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'failed', 'error': str(e)}}
        )
        
        # Send error status
        try:
            requests.post("http://localhost:8000/send-whatsapp-status", json={
                "user_id": "default_user",
                "message": f"❌ Failed to send WhatsApp: {str(e)}",
                "status_type": "error"
            })
        except:
            pass
        
        error_msg = f"❌ Failed to send WhatsApp: {str(e)}"
        print(f"📱 {error_msg}")
        return error_msg

@celery_app.task
def send_whatsapp_delayed(task_id: str, to_number: str, message: str):
    """
    Send delayed WhatsApp message
    """
    try:
        print(f"📱 SENDING DELAYED WHATSAPP to {to_number}")
        
        pywhatkit.sendwhatmsg_instantly(
            phone_no=to_number,
            message=message,
            wait_time=15,
            tab_close=True
        )
        
        # Update task status
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'sent', 'sent_at': datetime.now()}}
        )
        
        print(f"✅ Delayed WhatsApp sent to {to_number}")
        return f"Message sent to {to_number}"
        
    except Exception as e:
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'failed', 'error': str(e)}}
        )
        error_msg = f"❌ Failed to send delayed message: {str(e)}"
        print(f"📱 {error_msg}")
        return error_msg