"""
OCR Service using Azure Document Intelligence.
Extracts CIL (Customer Identification Number) from uploaded images.
"""
from typing import Optional
import io
from config.settings import settings


def extract_cil_from_image(image_bytes: bytes) -> Optional[str]:
    """
    Extract CIL from an image using Azure Document Intelligence.
    
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
            analyze_request=image_bytes,
            content_type="application/octet-stream"
        )
        
        result = poller.result()
        
        # Extract all text content
        extracted_text = ""
        if result.content:
            extracted_text = result.content
        
        # Simple pattern matching for CIL (assuming it's an 8-digit number)
        import re
        cil_pattern = r'\b\d{8}\b'
        matches = re.findall(cil_pattern, extracted_text)
        
        if matches:
            # Return the first 8-digit number found
            return matches[0]
        
        # If no 8-digit number found, return all extracted text for debugging
        return extracted_text if extracted_text else None
        
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
            analyze_request=image_bytes,
            content_type="application/octet-stream"
        )
        
        result = poller.result()
        
        if result.content:
            return result.content
        
        return None
        
    except Exception as e:
        print(f"Error in text extraction: {str(e)}")
        return None
