"""
Text-to-Speech Utility
========================
Converts text to speech using IBM Watson TTS API.
Falls back to browser's built-in TTS if IBM Watson is not configured.

IBM Watson TTS Documentation:
https://cloud.ibm.com/apidocs/text-to-speech
"""

import os
import tempfile
from typing import Optional

# IBM Watson SDK
try:
    from ibm_watson import TextToSpeechV1
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
    IBM_AVAILABLE = True
except ImportError:
    IBM_AVAILABLE = False


class TextToSpeech:
    """
    Text-to-Speech converter using IBM Watson.
    
    Setup:
    1. Create a free IBM Cloud account at cloud.ibm.com
    2. Create a Text to Speech service instance
    3. Copy your API key and service URL to .env file
    
    Available voices:
    - en-US_AllisonV3Voice (female)
    - en-US_MichaelV3Voice (male)
    - en-US_EmilyV3Voice (female)
    - en-GB_KateV3Voice (British female)
    """

    def __init__(self):
        self.tts_service = None
        self._setup_ibm_watson()

        # Directory to store generated audio files
        self.audio_dir = tempfile.gettempdir()

    def _setup_ibm_watson(self):
        """Initialize IBM Watson TTS service if credentials are available."""
        if not IBM_AVAILABLE:
            print("IBM Watson SDK not installed. TTS will use browser fallback.")
            return

        api_key = os.getenv('IBM_API_KEY')
        service_url = os.getenv('IBM_URL')

        if not api_key or not service_url:
            print("IBM Watson credentials not found in .env. TTS will use browser fallback.")
            return

        try:
            # Create authenticator with API key
            authenticator = IAMAuthenticator(api_key)

            # Create TTS service instance
            self.tts_service = TextToSpeechV1(authenticator=authenticator)

            # Set the service URL (from IBM Cloud dashboard)
            self.tts_service.set_service_url(service_url)

            print("IBM Watson TTS initialized successfully!")

        except Exception as e:
            print(f"IBM Watson TTS setup failed: {e}")
            self.tts_service = None

    def synthesize(self, text: str, voice: str = 'en-US_AllisonV3Voice') -> Optional[str]:
        """
        Convert text to speech and save as MP3 file.
        
        Args:
            text: Text to convert to speech
            voice: IBM Watson voice identifier
            
        Returns:
            Path to the generated audio file, or None if failed
        """
        if not self.tts_service:
            return None

        try:
            # Limit text length to avoid API limits
            # IBM Watson free tier has limits per call
            text = text[:2000] if len(text) > 2000 else text

            # Call IBM Watson TTS API
            response = self.tts_service.synthesize(
                text=text,
                voice=voice,
                accept='audio/mp3'  # Output format
            ).get_result()

            # Save the audio to a temporary file
            audio_path = os.path.join(self.audio_dir, 'studyassist_tts.mp3')

            with open(audio_path, 'wb') as audio_file:
                audio_file.write(response.content)

            return audio_path

        except Exception as e:
            print(f"TTS synthesis error: {e}")
            return None

    def get_available_voices(self) -> list:
        """Get list of available TTS voices."""
        return [
            {"id": "en-US_AllisonV3Voice", "name": "Allison (US English, Female)"},
            {"id": "en-US_MichaelV3Voice", "name": "Michael (US English, Male)"},
            {"id": "en-US_EmilyV3Voice", "name": "Emily (US English, Female)"},
            {"id": "en-US_HenryV3Voice", "name": "Henry (US English, Male)"},
            {"id": "en-GB_KateV3Voice", "name": "Kate (British English, Female)"},
            {"id": "en-AU_CraigVoice", "name": "Craig (Australian English, Male)"},
        ]

    def is_available(self) -> bool:
        """Check if IBM Watson TTS is configured and ready."""
        return self.tts_service is not None
