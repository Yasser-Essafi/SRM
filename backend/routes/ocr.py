"""
OCR API endpoints for bill image processing.
"""
from flask import Blueprint, request, jsonify
from services.ocr_service import extract_contract_from_image, extract_bill_information, format_extracted_info_arabic

ocr_bp = Blueprint('ocr', __name__)


@ocr_bp.route('/ocr/extract-contract', methods=['POST'])
def extract_contract():
    """
    Extract N°Contrat only from uploaded bill image.
    
    Form Data:
        file: Image file (jpg, png, pdf)
    
    Returns:
        JSON: Extracted contract number
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file uploaded',
                'error_ar': 'لم يتم رفع أي ملف'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'Empty filename',
                'error_ar': 'اسم الملف فارغ'
            }), 400
        
        # Read file bytes
        image_bytes = file.read()
        
        # Extract Contract Number
        contract = extract_contract_from_image(image_bytes)
        
        if not contract:
            return jsonify({
                'error': 'Contract number not found in image',
                'error_ar': 'لم يتم العثور على رقم العقد في الصورة'
            }), 404
        
        return jsonify({
            'contract': contract,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_ar': 'حدث خطأ في معالجة الصورة'
        }), 500


@ocr_bp.route('/ocr/extract-full', methods=['POST'])
def extract_full():
    """
    Extract full bill information from uploaded image.
    
    Form Data:
        file: Image file (jpg, png, pdf)
    
    Returns:
        JSON: Complete bill information
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file uploaded',
                'error_ar': 'لم يتم رفع أي ملف'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'Empty filename',
                'error_ar': 'اسم الملف فارغ'
            }), 400
        
        # Read file bytes
        image_bytes = file.read()
        
        # Extract full information
        bill_info = extract_bill_information(image_bytes)
        
        if 'error' in bill_info:
            return jsonify({
                'error': bill_info['error'],
                'error_ar': 'فشل استخراج المعلومات'
            }), 500
        
        # Format for display
        formatted_arabic = format_extracted_info_arabic(bill_info)
        
        return jsonify({
            'bill_info': bill_info,
            'formatted_ar': formatted_arabic,
            'status': 'success'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_ar': 'حدث خطأ في معالجة الصورة'
        }), 500
