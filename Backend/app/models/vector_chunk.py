# app/models/vector_chunk.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from .base import BaseModel

import logging

logger = logging.getLogger(__name__)

class VectorChunk(BaseModel):
    collection_name = 'vector_chunks'

    async def create_chunk(
            self,
            document_id: str,
            user_id: str,
            chunk_index: int,
            text_content: str,
            vector_embedding: List[float],
            metadata: Optional[Dict[str, Any]] = None
    ) -> ObjectId:
        """Create a new vector chunk."""
        chunk = {
            'document_id': ObjectId(document_id),
            'user_id': ObjectId(user_id),
            'chunk_index': chunk_index,
            'text_content': text_content,
            'vector_embedding': vector_embedding,
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'last_accessed': datetime.utcnow()
        }
        return await self.insert_one(chunk)

    async def find_similar_chunks(
            self,
            user_id: str,
            vector: List[float],
            limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar chunks using vector similarity."""
        pipeline = [
            {
                '$search': {
                    'index': 'vector_index',
                    'knnBeta': {
                        'vector': vector,
                        'path': 'vector_embedding',
                        'k': limit
                    }
                }
            },
            {
                '$match': {
                    'user_id': ObjectId(user_id)
                }
            },
            {
                '$limit': limit
            }
        ]

        try:
            results = await self.collection.aggregate(pipeline).to_list(length=limit)
            return results
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            raise
