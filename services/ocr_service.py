"""
OCR Service using Azure Document Intelligence.
Extracts CIL and other information from utility bills.
"""
from typing import Optional, Dict, Any
import re
from config.settings import settings


def extract_cil_from_image(image_bytes: bytes) -> Optional[str]:
    """
    Extract CIL from an image using Azure Document Intelligence.
    
    CIL Format: 1071324-101 (7 digits - 3 digits) or 7-10 digits
    
    Args:
        image_bytes: Image file bytes
        
    Returns:
        str: Extracted CIL number or None if extraction fails
    """
    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
        
        # Initialize the Document Intelligence client
        client = DocumentIntelligenceClient(
            endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)
        )
        
        # Analyze the document
        poller = client.begin_analyze_document(
            "prebuilt-read",
            body=image_bytes,
            content_type="application/octet-stream"
        )
        
        result = poller.result()
        
        # Extract all text content
        extracted_text = ""
        if result.content:
            extracted_text = result.content
        
        # Pattern matching for CIL
        # Primary format: 1071324-101 (7 digits - 3 digits)
        # Also match reversed: 101-1071324 (3 digits - 7 digits) and auto-correct it
        cil_patterns = [
            r'(?:CIL|N°\s*Client|رقم\s*العميل|Client\s*ID)\s*:?\s*(\d{3,7}-\d{3,7})',  # Any dash format
            r'\b(\d{3,7}-\d{3,7})\b',  # Standalone with dash
            r'(?:CIL|N°\s*Client|رقم\s*العميل|Client\s*ID)\s*:?\s*(\d{7,10})',  # 7-10 digits no dash
            r'\b(\d{8,10})\b'  # Fallback: 8-10 digit number
        ]
        
        for pattern in cil_patterns:
            matches = re.findall(pattern, extracted_text, re.IGNORECASE)
            if matches:
                cil = matches[0]
                # Fix reversed CIL: if format is 3digits-7digits, reverse it to 7digits-3digits
                if '-' in cil:
                    parts = cil.split('-')
                    if len(parts) == 2:
                        # If first part is 3 digits and second is 7, it's reversed
                        if len(parts[0]) == 3 and len(parts[1]) == 7:
                            cil = f"{parts[1]}-{parts[0]}"  # Reverse: 101-1071324 → 1071324-101
                        # Already correct format (7-3), keep as is
                return cil
        
        # If no pattern matched, return None
        return None
        
    except Exception as e:
        print(f"Error in OCR extraction: {str(e)}")
        return None


def extract_text_from_image(image_bytes: bytes) -> Optional[str]:
    """
    Extract all text from an image using Azure Document Intelligence.
    
    Args:
        image_bytes: Image file bytes
        
    Returns:
        str: Extracted text or None if extraction fails
    """
    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
        
        client = DocumentIntelligenceClient(
            endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)
        )
        
        poller = client.begin_analyze_document(
            "prebuilt-read",
            body=image_bytes,
            content_type="application/octet-stream"
        )
        
        result = poller.result()
        
        if result.content:
            return result.content
        
        return None
        
    except Exception as e:
        print(f"Error in text extraction: {str(e)}")
        return None


def extract_bill_information(image_bytes: bytes) -> Dict[str, Any]:
    """
    Extract comprehensive information from utility bill image.
    
    This function extracts:
    - CIL (Customer Identification Number)
    - Customer Name
    - Amount Due
    - Due Date
    - Bill Date
    - Service Type (Water/Electricity)
    - Previous Balance
    - Current Consumption
    
    Args:
        image_bytes: Image file bytes of the utility bill
        
    Returns:
        dict: Extracted information with keys:
            - cil: Customer ID (format: 1071324-101)
            - name: Customer name
            - amount_due: Amount to pay
            - due_date: Payment due date
            - bill_date: Bill issue date
            - service_type: Type of service
            - previous_balance: Previous unpaid balance
            - consumption: Current period consumption
            - raw_text: Full extracted text
    """
    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
        
        # Initialize client
        client = DocumentIntelligenceClient(
            endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)
        )
        
        # Analyze document
        poller = client.begin_analyze_document(
            "prebuilt-read",
            body=image_bytes,
            content_type="application/octet-stream"
        )
        
        result = poller.result()
        
        if not result.content:
            return {"error": "No text found in image"}
        
        text = result.content
        
        # Initialize result dictionary
        extracted_info = {
            "cil": None,
            "name": None,
            "amount_due": None,
            "due_date": None,
            "bill_date": None,
            "service_type": None,
            "previous_balance": None,
            "consumption": None,
            "raw_text": text
        }
        
        # Extract CIL (Format: 1071324-101 or 7-10 digits with optional dash)
        # Common patterns: "CIL: 1071324-101", "N° Client: 1071324-101", "رقم العميل: 1071324-101"
        cil_patterns = [
            r'(?:CIL|N°\s*Client|رقم\s*العميل|Client\s*ID|Identifiant)\s*:?\s*(\d{7}-\d{3})',  # Format: 1071324-101
            r'(?:CIL|N°\s*Client|رقم\s*العميل|Client\s*ID|Identifiant)\s*:?\s*(\d{3}-\d{7})',  # Reversed: 101-1071324
            r'(?:CIL|N°\s*Client|رقم\s*العميل|Client\s*ID|Identifiant)\s*:?\s*(\d{7,10})',  # 7-10 digits
            r'\b(\d{7}-\d{3})\b',  # Standalone format: 1071324-101
            r'\b(\d{3}-\d{7})\b',  # Standalone reversed: 101-1071324
            r'\b(\d{8,10})\b'  # Fallback: 8-10 digit number
        ]
        
        for pattern in cil_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cil = match.group(1)
                # Fix reversed CIL: if format is 3digits-7digits, reverse it to 7digits-3digits
                if '-' in cil:
                    parts = cil.split('-')
                    if len(parts) == 2:
                        # If first part is 3 digits and second is 7, it's reversed
                        if len(parts[0]) == 3 and len(parts[1]) == 7:
                            cil = f"{parts[1]}-{parts[0]}"  # Reverse to correct format
                extracted_info["cil"] = cil
                break
        
        # Extract Customer Name
        # Look for common name patterns in Arabic or French (including multi-word names)
        name_patterns = [
            r'(?:Nom|الاسم|Name)\s*:?\s*([A-Za-zÀ-ÿأ-ي\s]{3,50})',
            r'([A-Z][a-zà-ÿ]+\s+(?:EL\s+)?[A-Z][A-ZÀ-Ÿa-zà-ÿ]+)',  # Pattern: "Abdenbi EL MARZOUKI"
            r'(?:Client|العميل)\s*:?\s*([A-Za-zÀ-ÿأ-ي\s]{3,50})'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Clean up: remove if it's just numbers or too short
                if len(name) > 3 and not name.isdigit():
                    extracted_info["name"] = name
                    break
        
        # Extract Amount Due
        # Patterns for Redal bills: "Total Encaissé Dirhams: 351.48", "Montant Dirhams: 351.48"
        amount_patterns = [
            r'(?:Total\s+Encaissé?\s+Dirhams?|مجموع\s+محصل\s+درهم)\s*:?\s*([\d,\.]+)',  # Redal format
            r'(?:Montant\s+Dirhams?|مجموع\s+درهم)\s*:?\s*([\d,\.]+)',  # Alternative format
            r'(?:Montant|المبلغ|Amount|Total)\s*(?:à\s*payer|المستحق|Due)?\s*:?\s*([\d,\.]+)\s*(?:DH|درهم|MAD)?',
            r'([\d,\.]+)\s*(?:DH|درهم|MAD)\s*$'  # Amount at end of line
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    extracted_info["amount_due"] = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Extract Due Date
        # Patterns for Redal: "Date du paiement: 10-07-2013", dates in format DD-MM-YYYY or DD/MM/YYYY
        date_patterns = [
            r'(?:Date\s+du\s+paiement|تاريخ\s+الاتمام)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # Redal format
            r'(?:Date\s*limite|تاريخ\s*الاستحقاق|Due\s*Date|Échéance)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})'  # Standalone date
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_info["due_date"] = match.group(1)
                break
        
        # Extract Service Type
        # Look for keywords in Redal bills: "Eau et Assainissement", "Électricité", "ماء", "كهرباء"
        service_types = []
        if re.search(r'\b(?:Eau\s+et\s+Assainissement|Eau|ماء|الماء|Water)\b', text, re.IGNORECASE):
            service_types.append("ماء")
        if re.search(r'\b(?:Électricité|Electricité|كهرباء|Electricity)\b', text, re.IGNORECASE):
            service_types.append("كهرباء")
        
        if service_types:
            extracted_info["service_type"] = " و".join(service_types)  # "ماء وكهرباء" if both
        
        # Extract Consumption
        # Patterns: "Consommation: 150 m³", "الاستهلاك: 150 كيلووات"
        consumption_patterns = [
            r'(?:Consommation|الاستهلاك|Consumption)\s*:?\s*([\d,\.]+)\s*(?:m³|kWh|كيلووات)?'
        ]
        
        for pattern in consumption_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                consumption_str = match.group(1).replace(',', '.')
                try:
                    extracted_info["consumption"] = float(consumption_str)
                    break
                except ValueError:
                    continue
        
        # Extract detailed amounts for water and electricity (Redal specific)
        water_match = re.search(r'(?:Eau\s+et\s+Assainissement|الماء\s+والتطهير).*?([\d,\.]+)', text, re.IGNORECASE)
        elec_match = re.search(r'(?:Electricité|كهرباء).*?([\d,\.]+)', text, re.IGNORECASE)
        
        if water_match or elec_match:
            extracted_info["breakdown"] = {}
            if water_match:
                try:
                    extracted_info["breakdown"]["water"] = float(water_match.group(1).replace(',', '.'))
                except ValueError:
                    pass
            if elec_match:
                try:
                    extracted_info["breakdown"]["electricity"] = float(elec_match.group(1).replace(',', '.'))
                except ValueError:
                    pass
        
        return extracted_info
        
    except Exception as e:
        print(f"Error in bill information extraction: {str(e)}")
        return {"error": str(e), "raw_text": None}


def format_extracted_info_arabic(info: Dict[str, Any]) -> str:
    """
    Format extracted bill information in Arabic for display.
    
    Args:
        info: Dictionary of extracted information
        
    Returns:
        str: Formatted text in Arabic
    """
    if "error" in info:
        return f"❌ خطأ في استخراج المعلومات: {info['error']}"
    
    lines = ["📄 **المعلومات المستخرجة من الفاتورة:**\n"]
    
    if info.get("cil"):
        lines.append(f"🔢 رقم CIL: **{info['cil']}**")
    
    if info.get("name"):
        lines.append(f"👤 الاسم: {info['name']}")
    
    if info.get("service_type"):
        lines.append(f"⚡ نوع الخدمة: {info['service_type']}")
    
    if info.get("amount_due"):
        lines.append(f"💰 المبلغ المستحق: **{info['amount_due']:.2f} درهم**")
    
    # Show breakdown if available
    if info.get("breakdown"):
        if info["breakdown"].get("water"):
            lines.append(f"  └─ ماء: {info['breakdown']['water']:.2f} درهم")
        if info["breakdown"].get("electricity"):
            lines.append(f"  └─ كهرباء: {info['breakdown']['electricity']:.2f} درهم")
    
    if info.get("due_date"):
        lines.append(f"📅 تاريخ الاستحقاق: {info['due_date']}")
    
    if info.get("consumption"):
        lines.append(f"📊 الاستهلاك: {info['consumption']}")
    
    if info.get("previous_balance"):
        lines.append(f"💳 الرصيد السابق: {info['previous_balance']:.2f} درهم")
    
    return "\n".join(lines)

