import logging
from backend.voice.voice_engine import SimpleVoiceEngine

logger = logging.getLogger(__name__)

class VoiceManager:
    def __init__(self, dialogue_manager):
        self.voice_engine = SimpleVoiceEngine()
        self.dialogue_manager = dialogue_manager
        logger.info("✅ Voice manager ready!")
    
    async def start_voice_interaction(self):
        """Start a one-time voice conversation - NOW ASYNC"""
        try:
            # Greet user
            self.voice_engine.speak("Hello! I'm Nova. What would you like to know?")
            
            # Listen for command
            command = self.voice_engine.listen()
            
            if command == "timeout":
                self.voice_engine.speak("I didn't hear anything. Please try again.")
                return "No command received"
            elif command == "error":
                self.voice_engine.speak("Sorry, I had trouble understanding. Please try again.")
                return "Speech recognition error"
            else:
                # Process the command - NOW AWAIT PROPERLY
                return await self._process_voice_command("voice_user", command)
                
        except Exception as e:
            logger.error(f"❌ Voice interaction error: {e}")
            return f"Error: {str(e)}"
    
    async def _process_voice_command(self, user_id, command):
        """Process voice command and speak response"""
        try:
            # Use your existing dialogue manager WITH AWAIT
            response = await self.dialogue_manager.handle_message(user_id, command)
            
            # Simple tone detection
            tone = self._detect_tone(command)
            
            # Speak the response
            self.voice_engine.speak(response["reply"], tone)
            
            return response["reply"]
            
        except Exception as e:
            error_msg = "Sorry, I encountered an error processing your request."
            self.voice_engine.speak(error_msg)
            return f"{error_msg} {str(e)}"
    
    def _detect_tone(self, command):
        """Simple tone detection based on keywords"""
        command_lower = command.lower()
        
        if any(word in command_lower for word in ['joke', 'funny', 'laugh', 'haha']):
            return "funny"
        elif any(word in command_lower for word in ['chill', 'relax', 'calm', 'peaceful']):
            return "chill"
        elif any(word in command_lower for word in ['work', 'business', 'professional', 'serious']):
            return "professional"
        else:
            return "default"