# app/services/document_service.py
from app.services.base_service import BaseService
from app.utils.azure_storage import AzureStorageClient
from app.models.document import Document
from app.core.exceptions import AppException
from typing import List, Optional
import asyncio
import logging


logger = logging.getLogger(__name__)

class DocumentService(BaseService):
    def __init__(self):
        super().__init__()
        self.storage_client = AzureStorageClient()
        self.document_model = Document(self.db)

    async def upload_document(
            self,
            user_id: str,
            file_content: bytes,
            filename: str,
            content_type: str
    ):
        try:
            # Upload to Azure
            blob_name = self.storage_client.generate_blob_name(filename)
            blob_url = await self.storage_client.upload_blob(
                blob_name,
                file_content,
                content_type
            )

            # Create document record
            doc_id = await self.document_model.create_document(
                user_id=user_id,
                title=filename,
                azure_blob_name=blob_name,
                content_type=content_type,
                size=len(file_content),
                original_filename=filename
            )

            return {
                "document_id": str(doc_id),
                "blob_url": blob_url
            }

        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise AppException(f"Failed to upload document: {str(e)}")

    async def get_user_documents(self, user_id: str) -> List[dict]:
        try:
            documents = await self.document_model.get_user_documents(user_id)
            results = []

            for doc in documents:
                url = await self.storage_client.get_blob_url_with_sas(
                    doc['azure_blob_name']
                )
                doc['url'] = url
                results.append(doc)

            return results

        except Exception as e:
            logger.error(f"Error fetching user documents: {e}")
            raise AppException(f"Failed to fetch documents: {str(e)}")
