# backend/dialogue/follow_up_manager.py
from typing import List, Dict, Any
from backend.llm.context_manager import context_manager

class FollowUpManager:
    def __init__(self):
        self.context_manager = context_manager
    
    async def generate_follow_ups(self, user_id: str, session_key: str, current_response: str) -> List[str]:
        """Generate follow-ups for ANY conversation topic"""
        
        context = await self.context_manager.build_context_for_query(user_id, session_key, "")
        memory_summary = context.get("memory_summary", "")
        conversation_topic = context.get("conversation_topic", "general")
        
        follow_ups = []
        
        # GENERIC follow-up patterns
        follow_ups.extend(await self._get_information_follow_ups(memory_summary))
        follow_ups.extend(await self._get_assistance_follow_ups(memory_summary))
        follow_ups.extend(await self._get_planning_follow_ups(memory_summary))
        follow_ups.extend(await self._get_learning_follow_ups(memory_summary))
        follow_ups.extend(await self._get_entertainment_follow_ups(memory_summary))
        follow_ups.extend(await self._get_productivity_follow_ups(memory_summary))
        
        # Remove duplicates and return top 2
        unique_follow_ups = list(dict.fromkeys(follow_ups))
        return unique_follow_ups[:2]
    
    async def _get_information_follow_ups(self, context: str) -> List[str]:
        """Follow-ups for information-seeking conversations"""
        info_indicators = ["tell me", "what is", "how to", "explain", "information", "know about"]
        
        if any(indicator in context.lower() for indicator in info_indicators):
            return [
                "Would you like more detailed information about this?",
                "Should I find recent updates about this topic?",
                "Want me to compare different options?"
            ]
        return []
    
    async def _get_assistance_follow_ups(self, context: str) -> List[str]:
        """Follow-ups for task-oriented conversations"""
        task_indicators = ["help", "assist", "can you", "need", "want to", "looking for"]
        
        if any(indicator in context.lower() for indicator in task_indicators):
            return [
                "Would you like me to help with this?",
                "Should I break this down into steps?",
                "Need me to find resources for this task?"
            ]
        return []
    
    async def _get_planning_follow_ups(self, context: str) -> List[str]:
        """Follow-ups for planning conversations"""
        planning_indicators = ["plan", "schedule", "organize", "prepare", "arrange", "itinerary"]
        
        if any(indicator in context.lower() for indicator in planning_indicators):
            return [
                "Would you like me to create a plan for this?",
                "Should I set reminders for important dates?",
                "Need help scheduling this?"
            ]
        return []
    
    async def _get_learning_follow_ups(self, context: str) -> List[str]:
        """Follow-ups for learning conversations"""
        learning_indicators = ["learn", "study", "understand", "knowledge", "teach", "skill"]
        
        if any(indicator in context.lower() for indicator in learning_indicators):
            return [
                "Would you like me to suggest learning resources?",
                "Should I quiz you on this topic?",
                "Want practice exercises for this?"
            ]
        return []
    
    async def _get_entertainment_follow_ups(self, context: str) -> List[str]:
        """Follow-ups for entertainment topics"""
        entertainment_indicators = ["movie", "music", "show", "book", "game", "entertainment", "fun"]
        
        if any(indicator in context.lower() for indicator in entertainment_indicators):
            return [
                "Would you like recommendations?",
                "Should I find similar content?",
                "Want reviews or ratings?"
            ]
        return []
    
    async def _get_productivity_follow_ups(self, context: str) -> List[str]:
        """Follow-ups for productivity topics"""
        productivity_indicators = ["work", "task", "project", "deadline", "efficient", "productive"]
        
        if any(indicator in context.lower() for indicator in productivity_indicators):
            return [
                "Would you like productivity tips?",
                "Should I help prioritize tasks?",
                "Need time management suggestions?"
            ]
        return []
    
    async def generate_topic_specific_follow_ups(self, topic: str, user_preferences: Dict) -> List[str]:
        """Generate topic-specific follow-up questions"""
        topic_follow_ups = {
            "sports": [
                "Want to know recent scores?",
                "Should I find upcoming matches?",
                "Interested in player statistics?"
            ],
            "technology": [
                "Need technical specifications?",
                "Want latest news about this?",
                "Should I compare with alternatives?"
            ],
            "food": [
                "Want recipe suggestions?",
                "Should I find restaurants?",
                "Interested in nutrition information?"
            ],
            "travel": [
                "Need booking assistance?",
                "Want travel tips?",
                "Should I check weather forecasts?"
            ],
            "health": [
                "Want exercise routines?",
                "Need diet plans?",
                "Should I find healthcare providers?"
            ]
        }
        
        return topic_follow_ups.get(topic.lower(), [])

# Create global instance
follow_up_manager = FollowUpManager()