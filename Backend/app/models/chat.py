# app/models/chat.py
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from bson import ObjectId
from .base import BaseModel

import logging

logger = logging.getLogger(__name__)

class ChatThread(BaseModel):
    collection_name = 'chat_threads'

    async def create_thread(
            self,
            user_id: str,
            title: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None
    ) -> ObjectId:
        """Create a new chat thread."""
        thread = {
            'user_id': ObjectId(user_id),
            'title': title or "New Chat",
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'status': 'active',
            'context': context or {
                'documents': [],
                'summary': None
            }
        }
        return await self.insert_one(thread)

    async def get_user_threads(
            self,
            user_id: str,
            status: str = 'active',
            skip: int = 0,
            limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get chat threads for a specific user."""
        return await self.find_many(
            filter_dict={
                'user_id': ObjectId(user_id),
                'status': status
            },
            skip=skip,
            limit=limit,
            sort=[('updated_at', -1)]
        )


class ChatMessage(BaseModel):
    collection_name = 'chat_messages'

    async def create_message(
            self,
            thread_id: str,
            user_id: str,
            role: str,
            content: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> ObjectId:
        """Create a new chat message."""
        message = {
            'thread_id': ObjectId(thread_id),
            'user_id': ObjectId(user_id),
            'role': role,
            'content': content,
            'created_at': datetime.now(timezone.utc),
            'metadata': metadata or {}
        }
        message_id = await self.insert_one(message)

        # Update thread's updated_at timestamp
        await self.db['chat_threads'].update_one(
            {'_id': ObjectId(thread_id)},
            {'$set': {'updated_at': datetime.now(timezone.utc)}}
        )

        return message_id

    async def get_thread_messages(
            self,
            thread_id: str,
            skip: int = 0,
            limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages for a specific chat thread."""
        return await self.find_many(
            filter_dict={'thread_id': ObjectId(thread_id)},
            skip=skip,
            limit=limit,
            sort=[('created_at', 1)]
        )

