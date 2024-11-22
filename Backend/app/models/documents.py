# app/models/document.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from .base import BaseModel
import logging

logger = logging.getLogger(__name__)

class Document(BaseModel):
    collection_name = 'documents'

    async def create_document(
            self,
            user_id: str,
            title: str,
            azure_blob_name: str,
            content_type: str,
            size: int,
            original_filename: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> ObjectId:
        """Create a new document record."""
        document = {
            'user_id': ObjectId(user_id),
            'title': title,
            'azure_blob_name': azure_blob_name,
            'original_filename': original_filename,
            'content_type': content_type,
            'size': size,
            'upload_date': datetime.utcnow(),
            'status': 'processing',
            'metadata': metadata or {},
            'permissions': {
                'is_public': False,
                'shared_with': []
            }
        }
        return await self.insert_one(document)

    async def get_user_documents(
            self,
            user_id: str,
            status: Optional[str] = None,
            skip: int = 0,
            limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get documents for a specific user."""
        filter_dict = {'user_id': ObjectId(user_id)}
        if status:
            filter_dict['status'] = status

        return await self.find_many(
            filter_dict=filter_dict,
            skip=skip,
            limit=limit,
            sort=[('upload_date', -1)]
        )

    async def update_document_status(
            self,
            document_id: str,
            status: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update document status and metadata."""
        update_dict = {'status': status}
        if metadata:
            update_dict['metadata'] = metadata

        return await self.update_one(
            filter_dict={'_id': ObjectId(document_id)},
            update_dict=update_dict
        )
