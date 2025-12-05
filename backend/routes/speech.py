"""
Speech API endpoints for audio transcription.
"""
import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from services.speech_service import (
    recognize_speech_from_file,
    recognize_speech_from_bytes,
    get_supported_languages
)
from services.ai_service import initialize_agent, run_agent
from data.mock_db import (
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
        - Optional: 'language' field (default: ar-SA)
    
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
        language = request.form.get('language', 'ar-MA')
        
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
        - Optional: 'language' field (default: ar-MA)
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
        language = request.form.get('language', 'ar-MA')  # Defaults to Moroccan Arabic
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
