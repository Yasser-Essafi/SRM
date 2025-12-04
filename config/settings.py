"""
Configuration settings for SRM application.
Loads environment variables and provides application constants.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    
    # Azure Document Intelligence Configuration
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: Optional[str] = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    AZURE_DOCUMENT_INTELLIGENCE_KEY: Optional[str] = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    # Azure Speech Configuration
    AZURE_SPEECH_KEY: Optional[str] = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_REGION: Optional[str] = os.getenv("AZURE_SPEECH_REGION", "francecentral")
    # Application Constants
    APP_TITLE: str = "نظام خدمة العملاء - SRM"
    APP_ICON: str = "💧"
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate that all required settings are present.
        
        Returns:
            tuple: (is_valid, list_of_missing_keys)
        """
        missing_keys = []
        
        if not cls.AZURE_OPENAI_API_KEY:
            missing_keys.append("AZURE_OPENAI_API_KEY")
        if not cls.AZURE_OPENAI_ENDPOINT:
            missing_keys.append("AZURE_OPENAI_ENDPOINT")
        if not cls.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT:
            missing_keys.append("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        if not cls.AZURE_DOCUMENT_INTELLIGENCE_KEY:
            missing_keys.append("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        if not cls.AZURE_SPEECH_KEY:
            missing_keys.append("AZURE_SPEECH_KEY")
        is_valid = len(missing_keys) == 0
        return is_valid, missing_keys
    
    @classmethod
    def get_error_message(cls, missing_keys: list[str]) -> str:
        """
        Generate user-friendly error message for missing configuration.
        
        Args:
            missing_keys: List of missing environment variable names
            
        Returns:
            str: Formatted error message in Arabic and English
        """
        keys_str = ", ".join(missing_keys)
        return f"""
        ⚠️ خطأ في الإعدادات / Configuration Error
        
        المفاتيح التالية مفقودة في ملف .env:
        The following keys are missing in .env file:
        
        {keys_str}
        
        الرجاء نسخ ملف .env.example إلى .env وملء القيم المطلوبة.
        Please copy .env.example to .env and fill in the required values.
        """


# Create a singleton instance
settings = Settings()
