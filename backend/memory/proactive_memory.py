# backend/memory/proactive_memory.py
import datetime
from typing import List, Dict, Any
from backend.memory.memory_manager import MemoryManager

class ProactiveMemory:
    def __init__(self):
        self.memory_manager = MemoryManager()
    
    async def anticipate_user_needs(self, user_id: str, current_context: Dict) -> List[str]:
        """Anticipate needs for ANY topic dynamically"""
        
        memory_summary = current_context.get("memory_summary", "").lower()
        conversation_topic = current_context.get("conversation_topic", "general")
        
        anticipations = []
        
        # GENERIC anticipation patterns
        anticipations.extend(await self._detect_upcoming_events(memory_summary))
        anticipations.extend(await self._detect_preferences_needing_followup(memory_summary))
        anticipations.extend(await self._detect_questions_needing_answers(memory_summary))
        anticipations.extend(await self._detect_decisions_pending(memory_summary))
        anticipations.extend(await self._detect_learning_opportunities(memory_summary))
        
        return anticipations[:2]  # Return top 2 most relevant
    
    async def _detect_upcoming_events(self, context: str) -> List[str]:
        """Detect ANY upcoming events mentioned"""
        event_indicators = [
            "tomorrow", "next week", "next month", "coming", "upcoming", 
            "planning to", "going to", "will go", "scheduled", "appointment",
            "meeting", "deadline", "birthday", "anniversary", "trip", "travel"
        ]
        
        if any(indicator in context for indicator in event_indicators):
            return ["Would you like me to set a reminder for this?"]
        return []
    
    async def _detect_preferences_needing_followup(self, context: str) -> List[str]:
        """Detect ANY preferences that might need follow-up"""
        preference_indicators = [
            "prefer", "like", "love", "favorite", "enjoy", "admire", "hate",
            "dislike", "interested in", "passionate about", "fond of"
        ]
        
        if any(indicator in context for indicator in preference_indicators):
            return ["Want me to find more information about this?"]
        return []
    
    async def _detect_questions_needing_answers(self, context: str) -> List[str]:
        """Detect if user had unanswered questions"""
        question_indicators = ["?", "what", "how", "when", "where", "why", "can you", "could you"]
        
        if any(indicator in context for indicator in question_indicators):
            return ["Should I research this further for you?"]
        return []
    
    async def _detect_decisions_pending(self, context: str) -> List[str]:
        """Detect pending decisions"""
        decision_indicators = [
            "should i", "whether to", "can't decide", "not sure", 
            "thinking about", "considering", "trying to choose"
        ]
        
        if any(indicator in context for indicator in decision_indicators):
            return ["Would you like me to help you decide?"]
        return []
    
    async def _detect_learning_opportunities(self, context: str) -> List[str]:
        """Detect learning or skill development opportunities"""
        learning_indicators = [
            "learn", "study", "practice", "improve", "skill", "course",
            "tutorial", "master", "understand", "knowledge"
        ]
        
        if any(indicator in context for indicator in learning_indicators):
            return ["Would you like learning resources for this?"]
        return []
    
    async def get_context_based_suggestions(self, user_id: str, current_query: str, context: Dict) -> List[str]:
        """Get suggestions based on current conversation context"""
        suggestions = []
        
        # Check for location-based needs
        if any(word in context.get("memory_summary", "").lower() for word in ["go to", "visit", "travel", "trip"]):
            suggestions.extend([
                "Would you like directions?",
                "Need information about this place?"
            ])
        
        # Check for purchase decisions
        if any(word in context.get("memory_summary", "").lower() for word in ["buy", "purchase", "shop", "get"]):
            suggestions.extend([
                "Would you like price comparisons?",
                "Should I find reviews?"
            ])
        
        # Check for health/fitness topics
        if any(word in context.get("memory_summary", "").lower() for word in ["exercise", "diet", "health", "fitness"]):
            suggestions.extend([
                "Would you like a workout plan?",
                "Need nutrition advice?"
            ])
        
        return suggestions[:2]

# Create global instance
proactive_memory = ProactiveMemory()