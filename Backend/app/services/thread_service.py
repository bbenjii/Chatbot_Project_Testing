# app/services/thread_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from bson import ObjectId
import logging
from app.core.database import Database

from app.models.chatbot import ChatbotThread, ChatbotMessage
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class ThreadService:
    def __init__(self):
        self.db = Database.get_db()
        self.thread_model = ChatbotThread(self.db)
        self.message_model = ChatbotMessage(self.db)

    async def create_thread(
            self,
            user_id: str,
            title: Optional[str] = None,
            initial_message: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new chat thread."""
        try:
            # Generate default title if none provided
            if not title:
                title = f"Chatbot {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"

            # Create thread
            thread_id = await self.thread_model.create_thread(
                user_id=user_id,
                title=title,
                context=context
            )

            # Add initial message if provided
            if initial_message:
                await self.message_model.create_message(
                    thread_id=str(thread_id),
                    user_id=user_id,
                    role="user",
                    content=initial_message
                )

            # Get the created thread
            thread = await self.get_thread(str(thread_id))
            logger.info(f"Created new thread {thread_id} for user {user_id}")
            return thread

        except Exception as e:
            logger.error(f"Error creating thread: {e}")
            raise AppException(f"Failed to create thread: {str(e)}")

    async def get_thread(self, thread_id: str) -> Dict[str, Any]:
        """Get a specific thread with its messages."""
        try:
            # Get thread
            thread = await self.thread_model.find_one({"_id": ObjectId(thread_id)})
            if not thread:
                raise AppException("Thread not found", status_code=404)

            # Get messages for this thread
            messages = await self.message_model.get_thread_messages(thread_id)

            # Combine thread info with messages
            thread['messages'] = messages

            return thread

        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error fetching thread: {e}")
            raise AppException(f"Failed to fetch thread: {str(e)}")

    async def list_user_threads(
            self,
            user_id: str,
            skip: int = 0,
            limit: int = 20,
            status: str = 'active'
    ) -> List[Dict[str, Any]]:
        """List all threads for a user."""
        try:
            threads = await self.thread_model.find_many(
                filter_dict={
                    'user_id': ObjectId(user_id),
                    'status': status
                },
                skip=skip,
                limit=limit,
                sort=[('updated_at', -1)]  # Most recent first
            )

            # Add message count and last message for each thread
            # for thread in threads:
            #     thread['message_count'] = await self.message_model.count_documents({
            #         'thread_id': thread['_id']
            #     })
            #     last_message = await self.message_model.find_many(
            #         filter_dict={'thread_id': thread['_id']},
            #         sort=[('created_at', -1)]
            #     )
            #     thread['last_message'] = last_message

            return threads

        except Exception as e:
            logger.error(f"Error listing threads: {e}")
            raise AppException(f"Failed to list threads: {str(e)}")

    async def update_thread(
            self,
            thread_id: str,
            user_id: str,
            update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update thread information."""
        try:
            # Verify thread ownership
            thread = await self.thread_model.find_one({
                '_id': ObjectId(thread_id),
                'user_id': ObjectId(user_id)
            })
            if not thread:
                raise AppException("Thread not found or access denied", status_code=404)

            # Update thread
            update_data['updated_at'] = datetime.now(timezone.utc)
            success = await self.thread_model.update_one(
                {'_id': ObjectId(thread_id)},
                update_data
            )

            if not success:
                raise AppException("Failed to update thread")

            # Get updated thread
            return await self.get_thread(thread_id)

        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error updating thread: {e}")
            raise AppException(f"Failed to update thread: {str(e)}")

    async def delete_thread(self, thread_id: str, user_id: str) -> bool:
        """Delete a thread and all its messages."""
        try:
            # Start a transaction
            async with await self.db.client.start_session() as session:
                async with session.start_transaction():
                    # Verify thread ownership
                    thread = await self.thread_model.find_one({
                        '_id': ObjectId(thread_id),
                        'user_id': ObjectId(user_id)
                    })
                    if not thread:
                        raise AppException("Thread not found or access denied", status_code=404)

                    # Delete messages first
                    await self.message_model.delete_many({
                        'thread_id': ObjectId(thread_id)
                    })

                    # Delete thread
                    success = await self.thread_model.delete_one({
                        '_id': ObjectId(thread_id)
                    })

                    if not success:
                        raise AppException("Failed to delete thread")

                    logger.info(f"Deleted thread {thread_id} and its messages")
                    return True

        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error deleting thread: {e}")
            raise AppException(f"Failed to delete thread: {str(e)}")

    async def archive_thread(self, thread_id: str, user_id: str) -> Dict[str, Any]:
        """Archive a thread instead of deleting it."""
        try:
            return await self.update_thread(
                thread_id=thread_id,
                user_id=user_id,
                update_data={'status': 'archived'}
            )

        except Exception as e:
            logger.error(f"Error archiving thread: {e}")
            raise AppException(f"Failed to archive thread: {str(e)}")

    async def get_thread_messages(
            self,
            thread_id: str,
            skip: int = 0,
            limit: int = 50,
            sort_dir: int = 1  # 1 for ascending, -1 for descending
    ) -> List[Dict[str, Any]]:
        """Get messages for a specific thread with pagination."""
        try:
            messages = await self.message_model.find_many(
                filter_dict={'thread_id': ObjectId(thread_id)},
                skip=skip,
                limit=limit,
                sort=[('created_at', sort_dir)]
            )
            return messages

        except Exception as e:
            logger.error(f"Error fetching thread messages: {e}")
            raise AppException(f"Failed to fetch thread messages: {str(e)}")

    async def clear_thread_messages(self, thread_id: str, user_id: str) -> bool:
        """Clear all messages from a thread without deleting the thread itself."""
        try:
            # Verify thread ownership
            thread = await self.thread_model.find_one({
                '_id': ObjectId(thread_id),
                'user_id': ObjectId(user_id)
            })
            if not thread:
                raise AppException("Thread not found or access denied", status_code=404)

            # Delete all messages
            await self.message_model.delete_many({
                'thread_id': ObjectId(thread_id)
            })

            # Update thread
            await self.thread_model.update_one(
                {'_id': ObjectId(thread_id)},
                {
                    'updated_at': datetime.now(timezone.utc),
                    'last_message_at': datetime.now(timezone.utc)
                }
            )

            logger.info(f"Cleared all messages from thread {thread_id}")
            return True

        except AppException:
            raise
        except Exception as e:
            logger.error(f"Error clearing thread messages: {e}")
            raise AppException(f"Failed to clear thread messages: {str(e)}")


import asyncio

if __name__ == '__main__':
    async def main():
        await Database.connect()
        thread_service = ThreadService()

    #            user_id: str,
    #             title: Optional[str] = None,
    #             initial_message: Optional[str] = None,
    #             context: Optional[Dict[str, Any]] = None
        user_id = "673fefff00958834568c28d1"
        title = "Getting Started"
        initial_message = "Hey"

        # await thread_service.create_thread(user_id, title, initial_message)

    # asyncio.run(main())