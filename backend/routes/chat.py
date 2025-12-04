"""
Chat API endpoints for agent interactions.
"""
from flask import Blueprint, request, jsonify
from services.ai_service import initialize_agent, run_agent
from data.mock_db import (
    create_conversation, 
    get_conversation, 
    add_message_to_conversation,
    get_conversation_history
)

chat_bp = Blueprint('chat', __name__)

# Initialize agent once (singleton)
agent = None


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
    
    Request Body:
        {
            "message": "رقم CIL الخاص بي هو: 1071324-101",
            "conversation_id": "optional-uuid-string"
        }
    
    Returns:
        JSON: {
            "response": "...",
            "conversation_id": "uuid-string",
            "status": "success"
        }
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
        add_message_to_conversation(conversation_id, 'user', user_message)
        
        # Get agent
        agent_instance = get_agent()
        if not agent_instance:
            return jsonify({
                'error': 'Agent initialization failed',
                'error_ar': 'فشل تهيئة النظام'
            }), 500
        
        # Run agent with conversation history
        response = run_agent(agent_instance, user_message, chat_history)
        
        # Store assistant response
        add_message_to_conversation(conversation_id, 'assistant', response)
        
        return jsonify({
            'response': response,
            'conversation_id': conversation_id,
            'is_new_conversation': is_new_conversation,
            'status': 'success'
        }), 200
        
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
