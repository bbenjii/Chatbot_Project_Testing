# app_old/services/base_service.py
from app.core.database import Database
from app.core.exceptions import AppException
from typing import Optional, Any
from app.config import Settings

import logging

logger = logging.getLogger(__name__)

class BaseService:
    def __init__(self):
        self.db = Database.get_db()


import asyncio
# if __name__ == '__main__':
#     async def main():
#
#         await Database.connect()
#         service = BaseService()
#
#     asyncio.run(main())