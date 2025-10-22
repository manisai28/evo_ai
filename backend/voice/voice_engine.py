import pyttsx3
import speech_recognition as sr
import logging

logger = logging.getLogger(__name__)

class SimpleVoiceEngine:
    def __init__(self):
        try:
            self.tts = pyttsx3.init()
            self.recognizer = sr.Recognizer()
            logger.info("✅ Voice engine initialized successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize voice engine: {e}")
    
    def speak(self, text, tone="default"):
        """Convert text to speech with different tones"""
        try:
            # Simple tone adjustments
            if tone == "funny": 
                self.tts.setProperty('rate', 180)  # Faster
            elif tone == "chill": 
                self.tts.setProperty('rate', 120)  # Slower
            elif tone == "professional": 
                self.tts.setProperty('rate', 140)  # Moderate
            else:
                self.tts.setProperty('rate', 150)  # Default
            
            print(f"🔊 Speaking: {text}")
            self.tts.say(text)
            self.tts.runAndWait()
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
    
    def listen(self):
        """Listen to microphone and convert speech to text"""
        try:
            with sr.Microphone() as source:
                print("🎤 Listening... Speak now!")
                # Listen for 5 seconds max
                audio = self.recognizer.listen(source, timeout=10)
                text = self.recognizer.recognize_google(audio)
                print(f"🎤 Heard: {text}")
                return text
                
        except sr.WaitTimeoutError:
            print("⏰ Listening timeout")
            return "timeout"
        except Exception as e:
            logger.error(f"❌ Speech recognition error: {e}")
            return "error"