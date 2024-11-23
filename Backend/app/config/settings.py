# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "AI Productivity App"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Server settings
    HOST: str = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT: int = int(os.getenv('FLASK_PORT', 5000))

    # Database settings
    MONGODB_URL: str = os.getenv('MONGODB_URI')
    DB_NAME: str = os.getenv('DB_NAME')

    # Azure settings
    AZURE_STORAGE_ACCOUNT_NAME: str = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
    AZURE_STORAGE_ACCOUNT_KEY: str = os.getenv('AZURE_STORAGE_ACCESS_KEY')
    AZURE_STORAGE_CONTAINER: str = os.getenv('AZURE_STORAGE_CONTAINER', 'chatbot-storage')

    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT: str = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_KEY: str = os.getenv('AZURE_OPENAI_API_KEY')
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv('OPENAI_NAME')

    # Security settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_mongodb_settings(self):
        return {
            "url": self.MONGODB_URL,
            "db_name": self.DB_NAME
        }

    def get_azure_storage_settings(self):
        return {
            "account_name": self.AZURE_STORAGE_ACCOUNT_NAME,
            "account_key": self.AZURE_STORAGE_ACCOUNT_KEY,
            "container": self.AZURE_STORAGE_CONTAINER
        }


settings = Settings()