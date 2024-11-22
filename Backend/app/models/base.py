# app/models/base.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class BaseModel:
    collection_name: str = None

    def __init__(self, db):
        if self.collection_name is None:
            raise ValueError("collection_name must be set in derived class")
        self.db = db
        self.collection = self.db[self.collection_name]

    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            return await self.collection.find_one(filter_dict)
        except Exception as e:
            logger.error(f"Error in find_one: {e}")
            raise

    async def find_many(
            self,
            filter_dict: Dict[str, Any],
            skip: int = 0,
            limit: int = 0,
            sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        try:
            cursor = self.collection.find(filter_dict).skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)
            if sort:
                cursor = cursor.sort(sort)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error in find_many: {e}")
            raise

    async def insert_one(self, document: Dict[str, Any]) -> ObjectId:
        try:
            result = await self.collection.insert_one(document)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error in insert_one: {e}")
            raise

    async def update_one(
            self,
            filter_dict: Dict[str, Any],
            update_dict: Dict[str, Any],
            upsert: bool = False
    ) -> bool:
        try:
            result = await self.collection.update_one(
                filter_dict,
                {'$set': update_dict},
                upsert=upsert
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error in update_one: {e}")
            raise

    async def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        try:
            result = await self.collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error in delete_one: {e}")
            raise