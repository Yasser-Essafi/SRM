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
    
    # Azure SQL Database Configuration
    AZURE_SQL_SERVER: Optional[str] = os.getenv("AZURE_SQL_SERVER")
    AZURE_SQL_DATABASE: Optional[str] = os.getenv("AZURE_SQL_DATABASE")
    AZURE_SQL_USERNAME: Optional[str] = os.getenv("AZURE_SQL_USERNAME")
    AZURE_SQL_PASSWORD: Optional[str] = os.getenv("AZURE_SQL_PASSWORD")
    AZURE_SQL_DRIVER: str = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    
    # Application Constants
    APP_TITLE: str = "نظام خدمة العملاء - SRM"
    APP_ICON: str = "💧"
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate that all required settings are present.
        If using Windows Authentication (Trusted_Connection),
        AZURE_SQL_USERNAME and AZURE_SQL_PASSWORD are not required.
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
        if not cls.AZURE_SQL_SERVER:
            missing_keys.append("AZURE_SQL_SERVER")
        if not cls.AZURE_SQL_DATABASE:
            missing_keys.append("AZURE_SQL_DATABASE")

        # Only require username/password if at least one is non-empty (assume Trusted_Connection if both are empty)
        if (cls.AZURE_SQL_USERNAME or cls.AZURE_SQL_PASSWORD):
            if not cls.AZURE_SQL_USERNAME:
                missing_keys.append("AZURE_SQL_USERNAME")
            if not cls.AZURE_SQL_PASSWORD:
                missing_keys.append("AZURE_SQL_PASSWORD")

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
