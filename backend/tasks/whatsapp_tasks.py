import os
import time
from celery import Celery
from datetime import datetime, timedelta
from backend.core.database import sync_whatsapp_tasks_collection
from backend.core.celery_app import celery_app
from bson import ObjectId
import requests
from dotenv import load_dotenv

# Twilio for WhatsApp API
from twilio.rest import Client

def get_twilio_client():
    """Initialize Twilio client"""
    load_dotenv()
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    return Client(account_sid, auth_token)

@celery_app.task
def send_whatsapp_message(task_args):
    """
    Send WhatsApp message using Twilio API - PROPER Docker-compatible version
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
        
        # Schedule the actual sending
        if delay_minutes == 0:
            # Send immediately
            process_whatsapp_message.delay(str(task_id), to_number, message, user_id)
            return f"✅ WhatsApp queued for {to_number}"
        else:
            # Schedule for later
            process_whatsapp_message.apply_async(
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
    Process WhatsApp message using Twilio API
    """
    try:
        print(f"📱 PROCESSING WHATSAPP to {to_number}")
        
        # Update status to processing
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'processing', 'started_at': datetime.now()}}
        )
        
        # Send via Twilio WhatsApp API
        client = get_twilio_client()
        
        # Format number for Twilio (ensure it includes country code without +)
        formatted_number = to_number.replace('+', '')  # Twilio prefers no +
        
        # Send message via Twilio
        twilio_message = client.messages.create(
            body=message,
            from_='whatsapp:+14155238886',  # Twilio sandbox number
            to=f'whatsapp:{formatted_number}'
        )
        
        # Update task status to sent
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {
                'status': 'sent', 
                'sent_at': datetime.now(),
                'message_sid': twilio_message.sid
            }}
        )
        
        # Send success notification
        send_status_update(user_id, f"✅ WhatsApp sent successfully to {to_number}", "success")
        
        print(f"✅ WhatsApp sent to {to_number}, SID: {twilio_message.sid}")
        return f"Message sent to {to_number}"
        
    except Exception as e:
        # Update task status to failed
        sync_whatsapp_tasks_collection.update_one(
            {'_id': ObjectId(task_id)},
            {'$set': {'status': 'failed', 'error': str(e), 'failed_at': datetime.now()}}
        )
        
        error_msg = f"❌ Failed to send WhatsApp: {str(e)}"
        send_status_update(user_id, error_msg, "error")
        
        print(f"📱 {error_msg}")
        return error_msg

def send_status_update(user_id: str, message: str, status_type: str):
    """
    Helper function to send status updates to frontend
    """
    try:
        load_dotenv()
        requests.post(
            f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/send-whatsapp-status",
            json={
                "user_id": user_id,
                "message": message,
                "status_type": status_type
            },
            timeout=2
        )
    except Exception as e:
        print(f"⚠️ Could not send status update: {str(e)}")