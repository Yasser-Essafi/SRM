"""
OCR API endpoints for bill image processing.
"""
from flask import Blueprint, request, jsonify
from services.ocr_service import extract_contract_from_image, extract_bill_information, format_extracted_info_arabic

ocr_bp = Blueprint('ocr', __name__)


@ocr_bp.route('/ocr/extract-contract', methods=['POST'])
def extract_contract():
    """
    Extract water and/or electricity contract numbers from uploaded bill image.
    
    Form Data:
        file: Image file (jpg, png, pdf)
    
    Returns:
        JSON: Extracted contract numbers (water and/or electricity)
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file uploaded',
                'error_ar': 'لم يتم رفع ألم أتمكن من استخراج رقم العقد من الصورة.ي ملف'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'Empty filename',
                'error_ar': 'اسم الملف فارغ'
            }), 400
        
        # Read file bytes
        image_bytes = file.read()
        
        # Extract Contract Numbers (water and/or electricity)
        contracts = extract_contract_from_image(image_bytes)
        
        if not contracts:
            return jsonify({
                'water_contract': None,
                'electricity_contract': None,
                'status': 'not_found',
                'message': 'لم أتمكن من استخراج رقم العقد من الصورة. الرجاء التأكد من أن الصورة واضحة وتحتوي على رقم العقد، أو يمكنك كتابة الرقم مباشرة.',
                'message_en': 'I could not extract the contract number from the image. Please make sure the image is clear and contains the contract number, or you can type the number directly.',
                'message_fr': "Je n'ai pas pu extraire le numéro de contrat de l'image. Veuillez vous assurer que l'image est claire et contient le numéro de contrat, ou vous pouvez taper le numéro directement."
            }), 200
        
        return jsonify({
            'water_contract': contracts.get('water_contract'),
            'electricity_contract': contracts.get('electricity_contract'),
            'status': 'success'
        })
        
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
