"""
Azure Speech Service for speech-to-text and text-to-speech conversion.
Handles audio file recognition and speech synthesis.
"""
import os
import azure.cognitiveservices.speech as speechsdk
from typing import Optional, Tuple
from config.settings import settings


def recognize_speech_from_file(audio_file_path: str, language: str = None) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Recognize speech from an audio file using Azure Speech Service with auto language detection.
    
    Args:
        audio_file_path: Path to the audio file (WAV, MP3, OGG, etc.)
        language: Language code (optional). If None, auto-detects from multiple languages.
    
    Returns:
        tuple: (success: bool, transcribed_text: str, detected_language: str, error_message: str)
    """
    try:
        # Validate configuration
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return False, None, None, "Azure Speech credentials not configured"
        
        # Create speech configuration
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )
        
        # Create audio configuration from file
        audio_config = speechsdk.AudioConfig(filename=audio_file_path)
        
        # Create speech recognizer with auto-detection or specific language
        if language:
            # Use specified language
            speech_config.speech_recognition_language = language
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
        else:
            # Auto-detect language from multiple candidates (MAX 4 for Azure)
            # Priority: French first to avoid false Darija detection
            auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                languages=["fr-FR", "ar-MA", "ar-SA", "en-US"]
            )
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config,
                auto_detect_source_language_config=auto_detect_source_language_config
            )
        
        # Perform recognition
        result = speech_recognizer.recognize_once()
        
        # Get detected language if auto-detection was used
        detected_language = None
        if not language and result.reason == speechsdk.ResultReason.RecognizedSpeech:
            auto_detect_result = speechsdk.AutoDetectSourceLanguageResult(result)
            detected_language = auto_detect_result.language
        elif language:
            detected_language = language
        
        # Check result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return True, result.text, detected_language, None
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return False, None, None, "No speech detected in the audio file"
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_msg = f"Speech recognition canceled: {cancellation.reason}"
            if cancellation.reason == speechsdk.CancellationReason.Error:
                error_msg += f" - Error: {cancellation.error_details}"
            return False, None, None, error_msg
        else:
            return False, None, None, f"Unexpected result reason: {result.reason}"
            
    except Exception as e:
        return False, None, None, f"Exception during speech recognition: {str(e)}"


def recognize_speech_from_bytes(audio_data: bytes, audio_format: str = "wav", language: str = None) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Recognize speech from audio bytes in memory with auto language detection.
    
    Args:
        audio_data: Raw audio data as bytes
        audio_format: Audio format (wav, mp3, ogg, etc.)
        language: Language code (optional). If None, auto-detects from multiple languages.
    
    Returns:
        tuple: (success: bool, transcribed_text: str, detected_language: str, error_message: str)
    """
    try:
        # Validate configuration
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return False, None, None, "Azure Speech credentials not configured"
        
        # Create speech configuration
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )
        
        # Create push stream
        push_stream = speechsdk.audio.PushAudioInputStream()
        push_stream.write(audio_data)
        push_stream.close()
        
        # Create audio configuration from stream
        audio_config = speechsdk.AudioConfig(stream=push_stream)
        
        # Create speech recognizer with auto-detection or specific language
        if language:
            # Use specified language
            speech_config.speech_recognition_language = language
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
        else:
            # Auto-detect language from multiple candidates (MAX 4 for Azure)
            # Priority: French first to avoid false Darija detection
            auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                languages=["fr-FR", "ar-MA", "ar-SA", "en-US"]
            )
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config,
                auto_detect_source_language_config=auto_detect_source_language_config
            )
        
        # Perform recognition
        result = speech_recognizer.recognize_once()
        
        # Get detected language if auto-detection was used
        detected_language = None
        if not language and result.reason == speechsdk.ResultReason.RecognizedSpeech:
            auto_detect_result = speechsdk.AutoDetectSourceLanguageResult(result)
            detected_language = auto_detect_result.language
        elif language:
            detected_language = language
        
        # Check result
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return True, result.text, detected_language, None
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return False, None, None, "No speech detected in the audio"
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_msg = f"Speech recognition canceled: {cancellation.reason}"
            if cancellation.reason == speechsdk.CancellationReason.Error:
                error_msg += f" - Error: {cancellation.error_details}"
            return False, None, None, error_msg
        else:
            return False, None, None, f"Unexpected result reason: {result.reason}"
            
    except Exception as e:
        return False, None, None, f"Exception during speech recognition: {str(e)}"


def get_supported_languages() -> dict:
    """
    Get list of supported language codes for auto-detection.
    
    Returns:
        dict: Dictionary of language codes and names
    """
    return {
    "fr-FR": "Français",
    "ar-MA": "العربية (المغرب)",
    "ar-SA": "العربية (السعودية)",
    "en-US": "English (US)"
    }


def get_available_voices() -> dict:
    """
    Get available neural voices for text-to-speech.
    
    Returns:
        dict: Dictionary of language codes with available voices
    """
    return {
        "ar-MA": {
            "default": "ar-MA-JamalNeural",
            "voices": [
                {"name": "ar-MA-JamalNeural", "gender": "Male"},
                {"name": "ar-MA-MounaNeural", "gender": "Female"}
            ]
        },
        "ar-SA": {
            "default": "ar-SA-HamedNeural",
            "voices": [
                {"name": "ar-SA-HamedNeural", "gender": "Male"},
                {"name": "ar-SA-ZariyahNeural", "gender": "Female"}
            ]
        },
        "ar-EG": {
            "default": "ar-EG-ShakirNeural",
            "voices": [
                {"name": "ar-EG-ShakirNeural", "gender": "Male"},
                {"name": "ar-EG-SalmaNeural", "gender": "Female"}
            ]
        },
        "fr-FR": {
            "default": "fr-FR-HenriNeural",
            "voices": [
                {"name": "fr-FR-HenriNeural", "gender": "Male"},
                {"name": "fr-FR-DeniseNeural", "gender": "Female"}
            ]
        },
        "en-US": {
            "default": "en-US-GuyNeural",
            "voices": [
                {"name": "en-US-GuyNeural", "gender": "Male"},
                {"name": "en-US-JennyNeural", "gender": "Female"}
            ]
        }
    }


def text_to_speech(text: str, language: str = "ar-MA", voice: str = None) -> Tuple[bool, Optional[bytes], Optional[str]]:
    """
    Convert text to speech audio using Azure Speech Service.
    
    Args:
        text: Text to convert to speech
        language: Language code (default: ar-MA for Moroccan Arabic)
        voice: Specific voice name (optional, uses default for language if not specified)
    
    Returns:
        tuple: (success: bool, audio_data: bytes, error_message: str)
    """
    try:
        # Validate configuration
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return False, None, "Azure Speech credentials not configured"
        
        # Validate text
        if not text or not text.strip():
            return False, None, "Text cannot be empty"
        
        # Create speech configuration
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION
        )
        
        # Set voice
        available_voices = get_available_voices()
        if voice:
            speech_config.speech_synthesis_voice_name = voice
        elif language in available_voices:
            speech_config.speech_synthesis_voice_name = available_voices[language]["default"]
        else:
            # Fallback to Moroccan Arabic
            speech_config.speech_synthesis_voice_name = "ar-MA-JamalNeural"
        
        # Set output format to MP3
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        
        # Create synthesizer with no audio output (we want the bytes)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None  # No audio output, we want bytes
        )
        
        # Synthesize speech
        result = synthesizer.speak_text_async(text).get()
        
        # Check result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return True, result.audio_data, None
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            error_msg = f"Speech synthesis canceled: {cancellation.reason}"
            if cancellation.reason == speechsdk.CancellationReason.Error:
                error_msg += f" - Error: {cancellation.error_details}"
            return False, None, error_msg
        else:
            return False, None, f"Unexpected result: {result.reason}"
            
    except Exception as e:
        return False, None, f"Exception during speech synthesis: {str(e)}"
