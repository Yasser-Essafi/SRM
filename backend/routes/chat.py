"""
Chat API endpoints for agent interactions.
"""
import pyodbc
from config.settings import settings
from flask import Blueprint, request, jsonify, send_file
from io import BytesIO
from services.ai_service import initialize_agent, run_agent, extract_action

def _explicit_pay_intent(text: str) -> bool:
    t = (text or "").lower()
    keywords = [
        "أريد الدفع", "اريد الدفع", "بغيت نخلص", "نخلص", "خلص", "ادفع", "أدفع",
        "pay", "pay now", "payer", "paiement", "je veux payer"
    ]
    return any(k.lower() in t for k in keywords)

from services.speech_service import text_to_speech
from data.conversations import (
    create_conversation, 
    get_conversation, 
    add_message_to_conversation,
    get_conversation_history
)

chat_bp = Blueprint('chat', __name__)

# Initialize agent once (singleton)
agent = None


# Utility function to get DB connection
def get_connection():
    conn_str = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={settings.AZURE_SQL_SERVER};"
        f"Database={settings.AZURE_SQL_DATABASE};"
        f"Trusted_Connection=yes;"
        f"Encrypt=no;"
    )
    return pyodbc.connect(conn_str)


@chat_bp.route('/pay_invoice', methods=['POST'])
def pay_invoice():
    data = request.get_json() or {}
    contract_number = (data.get('contract_number') or "").strip()
    invoice_type = (data.get('invoice_type') or "electricity").strip().lower()

    if not contract_number:
        return jsonify({'success': False, 'message': 'Contract number required.'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if invoice_type == 'electricity':
            cursor.execute("""
                UPDATE dbo.electricity_invoices
                SET
                    is_paid = 1,
                    outstanding_balance = 0,
                    last_payment_datetime = SYSUTCDATETIME(),
                    last_payment_date = CONVERT(date, SYSUTCDATETIME()),
                    cut_status = 'OK',
                    cut_reason = NULL
                WHERE electricity_contract_number = ?
            """, contract_number)

        elif invoice_type == 'water':
            cursor.execute("""
                UPDATE dbo.water_invoices
                SET
                    is_paid = 1,
                    outstanding_balance = 0,
                    last_payment_datetime = SYSUTCDATETIME(),
                    last_payment_date = CONVERT(date, SYSUTCDATETIME()),
                    cut_status = 'OK',
                    cut_reason = NULL
                WHERE water_contract_number = ?
            """, contract_number)

        else:
            return jsonify({'success': False, 'message': 'Invalid invoice type.'}), 400

        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({'success': False, 'message': 'Contract not found.'}), 404

        conn.commit()
        return jsonify({'success': True, 'message': 'Paid successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def get_agent():
    """Get or create the AI agent."""
    global agent
    if agent is None:
        agent = initialize_agent()
    return agent

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for user messages.
    """
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing required field: message',
                'error_ar': 'الرجاء تقديم رسالة'
            }), 400

        user_message = data['message']
        conversation_id = data.get('conversation_id')
        language = data.get('language', 'ar')  # Default to Arabic

        # Create new conversation if no ID provided
        if not conversation_id:
            conversation_id = create_conversation()
            is_new_conversation = True
        else:
            conversation = get_conversation(conversation_id)
            if not conversation:
                return jsonify({
                    'error': 'Invalid conversation_id',
                    'error_ar': 'معرف المحادثة غير صالح'
                }), 404
            is_new_conversation = False

        # Get conversation history (without current message)
        chat_history = get_conversation_history(conversation_id)

        # Get agent
        agent_instance = get_agent()
        if not agent_instance:
            return jsonify({
                'error': 'Agent initialization failed',
                'error_ar': 'فشل تهيئة النظام'
            }), 500

        # 1) Main assistant response
        response_text = run_agent(agent_instance, user_message, chat_history, language)
        if not isinstance(response_text, str) or not response_text.strip():
            response_text = "عذراً، لم أتمكن من توليد رد واضح. هل يمكنك توضيح طلبك؟"


        # 2) Action extraction (from context)
        action = extract_action(user_message, chat_history)

        payload = {
            'status': 'success',
            'response': response_text,
            'conversation_id': conversation_id,
            'is_new_conversation': is_new_conversation,
        }

        if action.get("type") == "PAY_INVOICE":
            payload["action"] = {
                "type": "PAY_INVOICE",
                "contract_number": action.get("contract_number"),
                "invoice_type": action.get("invoice_type"),
            }
        elif action.get("type") == "NEED_CONTRACT":
            payload["action"] = {
                "type": "NEED_CONTRACT",   
                "invoice_type": action.get("invoice_type"),
            }

        # Store messages AFTER processing
        add_message_to_conversation(conversation_id, 'user', user_message)
        add_message_to_conversation(conversation_id, 'assistant', response_text)

        return jsonify(payload), 200

    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_ar': 'حدث خطأ في المعالجة'
        }), 500

@chat_bp.route('/chat/reset', methods=['POST'])
def reset_chat():
    """
    Reset chat session.
    
    Returns:
        JSON: Confirmation message
    """
    return jsonify({
        'message': 'Chat session reset',
        'message_ar': 'تم إعادة تعيين المحادثة',
        'status': 'success'
    }), 200


@chat_bp.route('/chat/history/<conversation_id>', methods=['GET'])
def get_history(conversation_id: str):
    """
    Get conversation history by conversation_id.
    
    Args:
        conversation_id: Unique conversation identifier
    
    Returns:
        JSON: Conversation history with all messages
    """
    try:
        conversation = get_conversation(conversation_id)
        
        if not conversation:
            return jsonify({
                'error': 'Conversation not found',
                'error_ar': 'المحادثة غير موجودة'
            }), 404
        
        return jsonify({
            'conversation_id': conversation_id,
            'created_at': conversation['created_at'],
            'messages': conversation['messages'],
            'message_count': len(conversation['messages']),
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_ar': 'حدث خطأ في جلب المحادثة'
        }), 500


@chat_bp.route('/chat/audio', methods=['POST'])
def chat_with_audio():
    """
    Chat endpoint that returns both text and audio response.
    
    Request Body:
        {
            "message": "رقم CIL الخاص بي هو: 1071324-101",
            "conversation_id": "optional-uuid-string",
            "language": "ar-MA",  // optional, default: ar-MA
            "voice": "ar-MA-JamalNeural"  // optional
        }
    
    Returns:
        Audio file (MP3) with the LLM response synthesized as speech.
        The conversation_id and response text are included in response headers.
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing required field: message',
                'error_ar': 'الرجاء تقديم رسالة'
            }), 400
        
        user_message = data['message']
        conversation_id = data.get('conversation_id')
        language = data.get('language', 'ar-MA')
        voice = data.get('voice')
        
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
        
        # Get conversation history (without current message)
        chat_history = get_conversation_history(conversation_id)
        
        # Get agent
        agent_instance = get_agent()
        if not agent_instance:
            return jsonify({
                'error': 'Agent initialization failed',
                'error_ar': 'فشل تهيئة النظام'
            }), 500
        
        # Run agent with conversation history
        response = run_agent(agent_instance, user_message, chat_history)
        
        # Store user message and assistant response
        add_message_to_conversation(conversation_id, 'user', user_message)
        add_message_to_conversation(conversation_id, 'assistant', response)
        
        # Convert response to speech
        success, audio_data, error = text_to_speech(response, language, voice)
        
        if not success:
            return jsonify({
                'error': error,
                'error_ar': 'فشل تحويل الرد إلى صوت',
                'response': response,
                'conversation_id': conversation_id
            }), 500
        
        # Create a BytesIO object from audio data
        audio_stream = BytesIO(audio_data)
        audio_stream.seek(0)
        
        # Return audio file with metadata in headers
        response_obj = send_file(
            audio_stream,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='chat_response.mp3'
        )
        
        # Add custom headers with conversation metadata
        response_obj.headers['X-Conversation-ID'] = conversation_id
        response_obj.headers['X-Is-New-Conversation'] = str(is_new_conversation).lower()
        response_obj.headers['X-Response-Text'] = response[:500]  # Truncate if too long
        
        return response_obj
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_ar': 'حدث خطأ في المعالجة'
        }), 500
