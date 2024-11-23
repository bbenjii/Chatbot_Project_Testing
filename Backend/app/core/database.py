# app/core/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging
import asyncio
from pymongo import IndexModel, ASCENDING, TEXT
from dotenv import load_dotenv

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)
load_dotenv()  # Load environment variables


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    async def connect(cls, mongodb_url: str = os.getenv("MONGODB_URI"), db_name: str = os.getenv("DB_NAME")):
        """Connect to MongoDB and initialize indexes."""
        try:
            cls.client = AsyncIOMotorClient(mongodb_url)
            cls.db = cls.client[db_name]

            # Verify connection
            await cls.client.admin.command('ping')
            logger.info("Connected to MongoDB")
            # print("Connected to MongoDB")

            # Initialize indexes
            await cls._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # print(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def _create_indexes(cls):
        """Create necessary indexes for all collections."""
        try:
            # Documents collection indexes
            await cls.db.documents.create_indexes([
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("upload_date", ASCENDING)]),
                IndexModel([("title", TEXT)])
            ])

            # Vector chunks collection indexes
            await cls.db.vector_chunks.create_indexes([
                IndexModel([("document_id", ASCENDING)]),
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("chunk_index", ASCENDING)])
            ])

            # Chat threads collection indexes
            await cls.db.assistant_threads.create_indexes([
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("updated_at", ASCENDING)]),
                IndexModel([("status", ASCENDING)])
            ])

            # Chat messages collection indexes
            await cls.db.assistant_messages.create_indexes([
                IndexModel([("thread_id", ASCENDING)]),
                IndexModel([("user_id", ASCENDING)]),
                IndexModel([("created_at", ASCENDING)])
            ])

            logger.info("Created MongoDB indexes")
            # print("Created MongoDB indexes")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            # print(f"Failed to create indexes: {e}")
            raise

    @classmethod
    async def close(cls):
        """Close the MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Closed MongoDB connection")
            # print("Closed MongoDB connection")

    @classmethod
    def get_db(cls):
        """Get the database instance."""
        if cls.db is None:
            # print("Database not initialized")
            raise RuntimeError("Database not initialized")
        return cls.db

#
# import asyncio
#
# if __name__ == '__main__':
#     async def main():
#         await Database.connect()
#         db = Database.get_db()
#
#     asyncio.run(main())