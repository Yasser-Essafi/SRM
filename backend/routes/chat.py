"""
Chat API endpoints for agent interactions.
"""
from flask import Blueprint, request, jsonify
from services.ai_service import initialize_agent, run_agent

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
            "chat_history": [
                {"role": "user", "content": "مرحبا"},
                {"role": "assistant", "content": "مرحبا بك"}
            ]
        }
    
    Returns:
        JSON: Agent response
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Missing required field: message',
                'error_ar': 'الرجاء تقديم رسالة'
            }), 400
        
        user_message = data['message']
        chat_history = data.get('chat_history', [])
        
        # Get agent
        agent_instance = get_agent()
        if not agent_instance:
            return jsonify({
                'error': 'Agent initialization failed',
                'error_ar': 'فشل تهيئة النظام'
            }), 500
        
        # Run agent
        response = run_agent(agent_instance, user_message, chat_history)
        
        return jsonify({
            'response': response,
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
