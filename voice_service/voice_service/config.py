"""
Voice Service configuration.

ElevenLabs Conversational AI configuration for voice alerts.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ElevenLabs configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "")
ELEVENLABS_PHONE_NUMBER_ID = os.getenv("ELEVENLABS_PHONE_NUMBER_ID", "")

# Voice service port
VOICE_SERVICE_PORT = int(os.getenv("VOICE_SERVICE_PORT", "8005"))
