"""
Health check endpoint.
"""
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON: Status and version information
    """
    return jsonify({
        'status': 'healthy',
        'service': 'SRM AI Customer Service',
        'version': '1.0.0'
    }), 200
