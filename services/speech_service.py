"""
Azure Speech Service for speech-to-text conversion.
Handles audio file recognition and real-time streaming.
"""
import os
import azure.cognitiveservices.speech as speechsdk
from typing import Optional, Tuple
from config.settings import settings


def recognize_speech_from_file(audio_file_path: str, language: str = "ar-SA") -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Recognize speech from an audio file using Azure Speech Service.
    
    Args:
        audio_file_path: Path to the audio file (WAV, MP3, OGG, etc.)
        language: Language code (default: ar-SA for Arabic Saudi Arabia)
                  Other options: ar-EG (Egyptian), ar-MA (Moroccan), fr-FR (French)
    
    Returns:
        tuple: (success: bool, transcribed_text: str, error_message: str)
    """
    try:
        # Validate configuration
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return False, None, "Azure Speech credentials not configured"
        
        # Create speech configuration
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )
        
        # Set recognition language
        speech_config.speech_recognition_language = language
        
        # Create audio configuration from file
        audio_config = speechsdk.AudioConfig(filename=audio_file_path)
        
        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # Perform recognition
        result = speech_recognizer.recognize_once()
        
        # Check result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return True, result.text, None
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return False, None, "No speech detected in the audio file"
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_msg = f"Speech recognition canceled: {cancellation.reason}"
            if cancellation.reason == speechsdk.CancellationReason.Error:
                error_msg += f" - Error: {cancellation.error_details}"
            return False, None, error_msg
        else:
            return False, None, f"Unexpected result reason: {result.reason}"
            
    except Exception as e:
        return False, None, f"Exception during speech recognition: {str(e)}"


def recognize_speech_from_bytes(audio_data: bytes, audio_format: str = "wav", language: str = "ar-SA") -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Recognize speech from audio bytes in memory.
    
    Args:
        audio_data: Raw audio data as bytes
        audio_format: Audio format (wav, mp3, ogg, etc.)
        language: Language code (default: ar-SA for Arabic)
    
    Returns:
        tuple: (success: bool, transcribed_text: str, error_message: str)
    """
    try:
        # Validate configuration
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return False, None, "Azure Speech credentials not configured"
        
        # Create speech configuration
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )
        
        # Set recognition language
        speech_config.speech_recognition_language = language
        
        # Create push stream
        push_stream = speechsdk.audio.PushAudioInputStream()
        push_stream.write(audio_data)
        push_stream.close()
        
        # Create audio configuration from stream
        audio_config = speechsdk.AudioConfig(stream=push_stream)
        
        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # Perform recognition
        result = speech_recognizer.recognize_once()
        
        # Check result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return True, result.text, None
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return False, None, "No speech detected in the audio"
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_msg = f"Speech recognition canceled: {cancellation.reason}"
            if cancellation.reason == speechsdk.CancellationReason.Error:
                error_msg += f" - Error: {cancellation.error_details}"
            return False, None, error_msg
        else:
            return False, None, f"Unexpected result reason: {result.reason}"
            
    except Exception as e:
        return False, None, f"Exception during speech recognition: {str(e)}"


def get_supported_languages() -> dict:
    """
    Get list of supported Arabic and French language codes.
    
    Returns:
        dict: Dictionary of language codes and names
    """
    return {
        "ar-SA": "العربية (السعودية)",
        "ar-EG": "العربية (مصر)",
        "ar-MA": "العربية (المغرب)",
        "ar-AE": "العربية (الإمارات)",
        "ar-DZ": "العربية (الجزائر)",
        "ar-TN": "العربية (تونس)",
        "fr-FR": "Français (France)",
        "fr-MA": "Français (Maroc)",
        "en-US": "English (US)"
    }
