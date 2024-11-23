# app/services/chatbot_service.py
import os
from dotenv import load_dotenv
from app.core.database import Database

from typing import Dict, Any
import logging
from app.core.chatbot_states import ChatbotStateMachine
from app.services.vector_service import VectorService
from app.services.thread_service import ThreadService
from app.core.exceptions import AppException
from app.services.base_service import BaseService
from datetime import datetime, timezone
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import message_chunk_to_message
from app.models.chatbot import ChatbotThread, ChatbotMessage

load_dotenv()  # load .env variables

logger = logging.getLogger(__name__)


class ChatbotService(BaseService):
    def __init__(self):
        super().__init__()
        # Initialize services
        # Initialize services
        self.thread_model = ChatbotThread(self.db)
        self.message_model = ChatbotMessage(self.db)

        self.vector_service = VectorService()
        self.thread_service = ThreadService()

        # Initialize Azure OpenAI
        try:
            self.model = AzureChatOpenAI(
                azure_deployment=os.getenv('OPENAI_NAME'),
                api_version=os.getenv('OPENAI_API_VERSION'),
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2,
                model=os.getenv('OPENAI_MODEL')
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI: {e}")
            raise AppException("Failed to initialize chatbot service")

        self.services = {
            'model': self.model,
            'vector_service': self.vector_service,
            'message_model': self.message_model,
            'thread_model': self.thread_model
        }

        # Initialize state machine
        self.state_machine = ChatbotStateMachine(self.services)

    async def process_message(
            self,
            user_id: str,
            thread_id: str,
            message: str
    ) -> Dict[str, Any]:
        """Process a message using the state machine."""
        try:
            # Get message history
            message_history = await self.message_model.get_thread_messages(
                thread_id=thread_id,
                limit=5  # Last 5 messages for context
            )

            # Process through state machine
            result = await self.state_machine.process_message(
                user_id=user_id,
                thread_id=thread_id,
                message=message,
                message_history=message_history
            )

            # Update thread
            await self.thread_model.update_one(
                {"_id": thread_id},
                {
                    "updated_at": datetime.now(timezone.utc),
                    "last_message_at": datetime.now(timezone.utc)
                }
            )

            return result

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise AppException(f"Failed to process message: {str(e)}")
import asyncio

if __name__ == '__main__':
    async def main():
        user_id = "673fefff00958834568c28d1"
        thread_id = "673ffd5434c80870f8c03364"
        message = "whats my full name?"

        await Database.connect()
        chatbot_service = ChatbotService()
        await chatbot_service.process_message(user_id=user_id, thread_id=thread_id, message=message)

    asyncio.run(main())