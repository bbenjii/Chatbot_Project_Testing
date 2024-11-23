# app/config/azure_storage.py
from pydantic_settings import BaseSettings
from typing import Optional
import os


class AzureStorageSettings(BaseSettings):
    AZURE_STORAGE_ACCOUNT_NAME: str
    AZURE_STORAGE_ACCOUNT_KEY: str
    AZURE_STORAGE_CONTAINER: str = "user-documents"

    # Optional settings.py
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = None
    AZURE_STORAGE_USE_CONNECTION_STRING: bool = False
    AZURE_STORAGE_SAS_EXPIRY_HOURS: int = 1

    # Container settings.py
    AZURE_STORAGE_MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    AZURE_STORAGE_ALLOWED_EXTENSIONS: set = {
        '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx',
        '.png', '.jpg', '.jpeg', '.gif'
    }

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def account_url(self) -> str:
        return f"https://{self.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"


azure_storage_settings = AzureStorageSettings()