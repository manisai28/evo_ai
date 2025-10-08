# backend/loggers/personalization_logger.py
import datetime
import json
from backend.core.database import db

logs_collection = db["personalization_logs"]

class PersonalizationLogger:
    @staticmethod
    async def log_interaction(user_id: str, input_text: str, output_text: str, metadata: dict = None):
        """
        Logs every interaction for personalization insights.
        """
        log_entry = {
            "user_id": user_id,
            "input": input_text,
            "output": output_text,
            "metadata": metadata or {},
            "timestamp": datetime.datetime.now()
        }
        await logs_collection.insert_one(log_entry)

    @staticmethod
    async def get_user_logs(user_id: str, limit=20):
        cursor = logs_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
