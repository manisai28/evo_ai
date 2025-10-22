from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from backend.tasks.whatsapp_tasks import send_whatsapp_message
from backend.core.database import sync_whatsapp_tasks_collection
from bson import ObjectId

router = APIRouter()

@router.post("/send-whatsapp/")
async def schedule_whatsapp_message(to_number: str, message: str, delay_minutes: int = 0, user_id: str = "default_user"):
    """
    Schedule a WhatsApp message to be sent
    """
    try:
        # Validate phone number (basic validation)
        if not to_number.startswith('+'):
            raise HTTPException(status_code=400, detail="Phone number must include country code (e.g., +91)")
        
        # Prepare task arguments
        task_args = {
            'to_number': to_number,
            'message': message,
            'delay_minutes': delay_minutes,
            'user_id': user_id
        }
        
        # Schedule the task
        result = send_whatsapp_message.delay(task_args)
        
        return {
            "status": "scheduled",
            "task_id": str(result.id),
            "message": f"Message scheduled to {to_number}",
            "delay_minutes": delay_minutes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling message: {str(e)}")

@router.get("/whatsapp-tasks/")
async def get_whatsapp_tasks():
    """
    Get all WhatsApp tasks
    """
    tasks = list(sync_whatsapp_tasks_collection.find().sort('created_at', -1).limit(50))
    
    # Convert ObjectId to string
    for task in tasks:
        task['_id'] = str(task['_id'])
        task['scheduled_time'] = task['scheduled_time'].isoformat()
        task['created_at'] = task['created_at'].isoformat()
        if task.get('sent_at'):
            task['sent_at'] = task['sent_at'].isoformat()
    
    return {"tasks": tasks}
