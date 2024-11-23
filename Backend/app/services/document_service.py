# app/services/document_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging
import mimetypes
from bson import ObjectId
import os
from app.services.base_service import BaseService
from app.services.vector_service import VectorService
from app.core.azure_storage import AzureStorageClient
from app.models.document import Document
from app.core.exceptions import AppException, DocumentNotFoundError
from app.utils.text_processor import TextProcessor
from app.core.database import Database

logger = logging.getLogger(__name__)


class DocumentService(BaseService):
    def __init__(self):
        super().__init__()
        self.storage_client = AzureStorageClient()
        self.document_model = Document(self.db)
        self.vector_service = VectorService()
        self.text_processor = TextProcessor()

    async def upload_document(
            self,
            user_id: str,
            file_content: bytes,
            filename: str,
            content_type: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload a document and process it for vector search."""
        try:
            # Validate file
            # self._validate_file(filename, content_type, len(file_content))

            # Upload to Azure
            blob_name = self.storage_client.generate_blob_name(filename, user_id)
            blob_url = await self.storage_client.upload_blob(
                blob_name=blob_name,
                file_content=file_content,
                content_type=content_type
            )

            # Create document record
            doc_id = await self.document_model.create_document(
                user_id=user_id,
                title=filename,
                azure_blob_name=blob_name,
                content_type=content_type,
                size=len(file_content),
                original_filename=filename,
                metadata=metadata
            )

            # Process document for vector search if applicable
            if self._should_vectorize(content_type):
                # Extract text from document
                text_content = await self._extract_text_content(
                    file_content,
                    content_type
                )

                # Process for vector search
                await self.vector_service.process_document(
                    document_id=str(doc_id),
                    user_id=user_id,
                    text_content=text_content,
                    metadata={
                                 "source_file": filename,
                                 "content_type": content_type,
                                 **(metadata or {})
                }
                )

                # Update document status
                await self.document_model.update_document_status(
                    str(doc_id),
                    "processed",
                    {"vectorized": True}
                )

            return {
                "document_id": str(doc_id),
                "blob_url": blob_url,
                "status": "processed"
            }

        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise AppException(f"Failed to upload document: {str(e)}")

    async def get_user_documents(
            self,
            user_id: str,
            skip: int = 0,
            limit: int = 50,
            status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all documents for a user with pagination."""
        try:
            documents = await self.document_model.get_user_documents(
                user_id=user_id,
                status=status,
                skip=skip,
                limit=limit
            )

            results = []
            for doc in documents:
                # Get SAS URL for each document
                url = await self.storage_client.get_blob_url_with_sas(
                    doc['azure_blob_name']
                )
                doc['url'] = url

                # Add vector stats if document is vectorized
                # if doc.get('metadata', {}).get('vectorized'):
                #     vector_stats = await self.vector_service.get_document_stats(
                #         document_id=str(doc['_id']),
                #         user_id=user_id
                #     )
                #     doc['vector_stats'] = vector_stats

                results.append(doc)

            return results

        except Exception as e:
            logger.error(f"Error fetching user documents: {e}")
            raise AppException(f"Failed to fetch documents: {str(e)}")

    async def get_document(
            self,
            document_id: str,
            user_id: str
    ) -> Dict[str, Any]:
        """Get a specific document by ID."""
        try:
            document = await self.document_model.find_one({
                '_id': ObjectId(document_id),
                'user_id': ObjectId(user_id)
            })

            if not document:
                raise DocumentNotFoundError()

            # Add SAS URL
            document['url'] = await self.storage_client.get_blob_url_with_sas(
                document['azure_blob_name']
            )

            return document

        except DocumentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching document: {e}")
            raise AppException(f"Failed to fetch document: {str(e)}")

    async def delete_document(
            self,
            document_id: str,
            user_id: str
    ) -> bool:
        """Delete a document and its associated data."""
        try:
            # Get document
            document = await self.get_document(document_id, user_id)

            # Delete from Azure Storage
            await self.storage_client.delete_blob(document['azure_blob_name'])

            # Delete vector embeddings if they exist
            if document.get('metadata', {}).get('vectorized'):
                await self.vector_service.delete_document_vectors(
                    document_id,
                    user_id
                )

            # Delete document record
            await self.document_model.delete_one({
                '_id': ObjectId(document_id),
                'user_id': ObjectId(user_id)
            })

            logger.info(f"Deleted document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise AppException(f"Failed to delete document: {str(e)}")

    async def update_document(
            self,
            document_id: str,
            user_id: str,
            update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update document metadata."""
        try:
            # Verify document exists and user has access
            document = await self.get_document(document_id, user_id)

            # Update document
            await self.document_model.update_one(
                {'_id': ObjectId(document_id)},
                {
                    **update_data,
                    'updated_at': datetime.now(timezone.utc)
                }
            )

            # Get updated document
            return await self.get_document(document_id, user_id)

        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise AppException(f"Failed to update document: {str(e)}")

    async def reprocess_document(
            self,
            document_id: str,
            user_id: str
    ) -> Dict[str, Any]:
        """Reprocess a document for vector search."""
        try:
            # Get document
            document = await self.get_document(document_id, user_id)

            # Download content from Azure
            file_content = await self.storage_client.download_blob(
                document['azure_blob_name']
            )

            # Extract text
            text_content = await self._extract_text_content(
                file_content,
                document['content_type']
            )

            # Reprocess vectors
            await self.vector_service.reprocess_document(
                document_id=document_id,
                user_id=user_id,
                text_content=text_content,
                metadata=document.get('metadata')
            )

            # Update document status
            return await self.update_document(
                document_id,
                user_id,
                {
                    'status': 'processed',
                    'metadata': {
                        **document.get('metadata', {}),
                        'vectorized': True,
                        'last_processed': datetime.now(timezone.utc).isoformat()
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error reprocessing document: {e}")
            raise AppException(f"Failed to reprocess document: {str(e)}")

    def _validate_file(self, filename: str, content_type: str, size: int):
        """Validate file before upload."""
        # Check file size (e.g., 50MB limit)
        max_size = 50 * 1024 * 1024  # 50MB
        if size > max_size:
            raise AppException("File size exceeds maximum limit")

        # Validate content type
        allowed_types = [
            'application/pdf',
            'text/plain',
            'text/markdown',
            'text/html',
            'application/json'
        ]

        if content_type not in allowed_types:
            raise AppException("Unsupported file type")

        # Validate file extension
        allowed_extensions = ['.pdf', '.txt', '.md', '.html', '.json']
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            raise AppException("Unsupported file extension")

    def _should_vectorize(self, content_type: str) -> bool:
        """Determine if a file should be vectorized based on content type."""
        vectorizable_types = [
            'application/pdf',
            'text/plain',
            'text/markdown',
            'text/html'
        ]
        return content_type in vectorizable_types

    async def _extract_text_content(
            self,
            file_content: bytes,
            content_type: str
    ) -> str:
        """Extract text content from file based on type."""
        try:
            if content_type == 'text/plain':
                return file_content.decode('utf-8')

            elif content_type == 'application/pdf':
                # Use PyPDF2 or similar to extract text
                return await self.text_processor.extract_text(file_content, "application/pdf")

            elif content_type in ['text/markdown', 'text/html']:
                # Use BeautifulSoup to extract text
                return self.text_processor.sanitize_text(
                    file_content.decode('utf-8')
                )

            raise AppException(f"Unsupported content type for text extraction: {content_type}")

        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            raise AppException(f"Failed to extract text content: {str(e)}")

import asyncio

if __name__ == '__main__':
    async def main():
        cv_path = "../../Test-Documents/ben-resumes/benollomo-cv.pdf"
        cover_letter_path = "../../Test-Documents/ben-resumes/benollomo-cover-letter.pdf"
        goku_1_path = "../../Test-Documents/images/picolo.jpeg"


        file = None
        with open(cv_path, "rb") as data:
            file = data.read()

        await Database.connect()

        service = DocumentService()
        # await service.upload_document("673fefff00958834568c28d1", file, "resume_benjamin_ollomo","application/pdf")
        print(await service.get_user_documents("673fefff00958834568c28d1"))
        # print(vector)

    asyncio.run(main())