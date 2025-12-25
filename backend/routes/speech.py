"""
Speech API endpoints for audio transcription.
"""
import os
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from io import BytesIO
from services.speech_service import (
    recognize_speech_from_file,
    recognize_speech_from_bytes,
    get_supported_languages,
    text_to_speech,
    get_available_voices
)
from services.ai_service import initialize_agent, run_agent
from data.conversations import (
    create_conversation,
    get_conversation,
    add_message_to_conversation,
    get_conversation_history
)

speech_bp = Blueprint('speech', __name__)

# Allowed audio file extensions - Only WAV format
ALLOWED_EXTENSIONS = {'wav'}
UPLOAD_FOLDER = 'uploads/audio'

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed. Accepts only WAV format."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@speech_bp.route('/speech/languages', methods=['GET'])
def get_languages():
    """
    Get supported languages for speech recognition.
    
    Returns:
        JSON: Dictionary of supported language codes and names
    """
    return jsonify({
        'languages': get_supported_languages(),
        'status': 'success'
    }), 200


@speech_bp.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """
    Convert audio file to text using Azure Speech Service.
    
    Request:
        - Multipart form data with 'audio' file
        - Optional: 'language' field (auto detected even if not provided))
    
    Returns:
        JSON: {
            "text": "transcribed text",
            "language": "ar-SA",
            "status": "success"
        }
    """
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                'error': 'No audio file provided',
                'error_ar': 'لم يتم تقديم ملف صوتي'
            }), 400
        
        audio_file = request.files['audio']
        
        # Check if file is selected
        if audio_file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'error_ar': 'لم يتم اختيار ملف'
            }), 400
        
        # Check file extension
        if not allowed_file(audio_file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}',
                'error_ar': 'نوع الملف غير مسموح به'
            }), 400
        
        # Get language parameter (optional, defaults to ar-MA)
        language = request.form.get('language', None)
        if language == '' or language == 'auto':
            language = None  # Let service auto-detect
        
        # Save file temporarily
        filename = secure_filename(audio_file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(file_path)
        
        try:
            # Recognize speech from file (with specified language)
            success, text, detected_language, error = recognize_speech_from_file(file_path, language)
            
            if success:
                return jsonify({
                    'text': text,
                    'language': detected_language,
                    'status': 'success'
                }), 200
            else:
                return jsonify({
                    'error': error,
                    'error_ar': 'فشل في التعرف على الصوت'
                }), 400
        finally:
            # Clean up: delete temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_ar': 'حدث خطأ في معالجة الصوت'
        }), 500


@speech_bp.route('/speech-to-chat', methods=['POST'])
def speech_to_chat():
    """
    Convert audio to text and send directly to chat agent.
    
    Request:
        - Multipart form data with 'audio' file
        - Optional: 'language' field (auto detected if not provided)
        - Optional: 'conversation_id' field
    
    Returns:
        JSON: {
            "transcribed_text": "...",
            "response": "...",
            "conversation_id": "...",
            "is_new_conversation": true/false,
            "status": "success"
        }
    """
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                'error': 'No audio file provided',
                'error_ar': 'لم يتم تقديم ملف صوتي'
            }), 400
        
        audio_file = request.files['audio']
        
        # Check if file is selected
        if audio_file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'error_ar': 'لم يتم اختيار ملف'
            }), 400
        
        # Check file extension
        if not allowed_file(audio_file.filename):
            return jsonify({
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}',
                'error_ar': 'نوع الملف غير مسموح به'
            }), 400
        
        # Get parameters
        language = request.form.get('language', None)  # Defaults to auto-detection
        if language == '' or language == 'auto':
            language = None  # Enable auto-detection
        conversation_id = request.form.get('conversation_id')
        
        # Save file temporarily
        filename = secure_filename(audio_file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        audio_file.save(file_path)
        
        try:
            # Step 1: Recognize speech from file (auto-detects language if not specified)
            success, transcribed_text, detected_language, error = recognize_speech_from_file(file_path, language)
            
            if not success:
                return jsonify({
                    'error': error,
                    'error_ar': 'فشل في التعرف على الصوت'
                }), 400
            
            # Step 2: Process with chat agent
            # Create new conversation if no ID provided
            if not conversation_id:
                conversation_id = create_conversation()
                is_new_conversation = True
            else:
                # Verify conversation exists
                conversation = get_conversation(conversation_id)
                if not conversation:
                    return jsonify({
                        'error': 'Invalid conversation_id',
                        'error_ar': 'معرف المحادثة غير صالح'
                    }), 404
                is_new_conversation = False
            
            # Get conversation history
            chat_history = get_conversation_history(conversation_id)
            
            # Store user message
            add_message_to_conversation(conversation_id, 'user', transcribed_text)
            
            # Get agent
            from routes.chat import get_agent
            agent_instance = get_agent()
            
            if not agent_instance:
                return jsonify({
                    'error': 'Agent initialization failed',
                    'error_ar': 'فشل تهيئة النظام'
                }), 500
            
            # Run agent with conversation history
            response = run_agent(agent_instance, transcribed_text, chat_history)
            
            # Store assistant response
            add_message_to_conversation(conversation_id, 'assistant', response)
            
            return jsonify({
                'transcribed_text': transcribed_text,
                'response': response,
                'conversation_id': conversation_id,
                'is_new_conversation': is_new_conversation,
                'language': detected_language,
                'status': 'success'
            }), 200
            
        finally:
            # Clean up: delete temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_ar': 'حدث خطأ في المعالجة'
        }), 500


@speech_bp.route('/synthesize/speech', methods=['POST'])
def text_to_speech_endpoint():
    """
    Convert text to speech audio using Azure Speech Service.
    Automatically detects language and selects appropriate voice:
    - French text → fr-FR-DeniseNeural
    - Arabic text → ar-MA-JamalNeural
    
    Request Body:
        {
            "text": "النص المراد تحويله إلى صوت"
        }
    
    Optional fields:
        - "language": "ar-MA" or "fr-FR" (overrides auto-detection)
        - "voice": specific voice name (overrides auto-selection)
    
    Returns:
        Audio file (MP3) with the synthesized speech
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text',
                'error_ar': 'الرجاء تقديم النص'
            }), 400
        
        text = data['text']
        language = data.get('language')  # Optional
        voice = data.get('voice')  # Optional
        
        # Ensure empty strings are treated as None
        if language == '' or language is None:
            language = None
        if voice == '' or voice is None:
            voice = None
        
        # AUTO-DETECT language if not provided
        if not language:
            import re
            arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
            if arabic_chars > 0:
                language = "ar-MA"
            else:
                language = "fr-FR"
        
        # AUTO-SELECT voice if not provided
        if not voice:
            if language == "ar-MA":
                voice = "ar-MA-JamalNeural"
            else:
                voice = "fr-FR-DeniseNeural"
        
        # Validate text is not empty
        if not text.strip():
            return jsonify({
                'error': 'Text cannot be empty',
                'error_ar': 'النص لا يمكن أن يكون فارغاً'
            }), 400
        
        # Convert text to speech
        success, audio_data, error = text_to_speech(text, language, voice)
        
        if not success:
            return jsonify({
                'error': error,
                'error_ar': 'فشل تحويل النص إلى صوت'
            }), 500
        
        # Create a BytesIO object from audio data
        audio_stream = BytesIO(audio_data)
        audio_stream.seek(0)
        
        # Return audio file
        return send_file(
            audio_stream,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='response.mp3'
        )
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_ar': 'حدث خطأ في المعالجة'
        }), 500


@speech_bp.route('/speech/voices', methods=['GET'])
def get_voices():
    """
    Get available neural voices for text-to-speech.
    
    Returns:
        JSON: Dictionary of language codes with available voices
    """
    return jsonify({
        'voices': get_available_voices(),
        'status': 'success'
    }), 200
