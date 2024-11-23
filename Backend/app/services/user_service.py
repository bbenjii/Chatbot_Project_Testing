# app/services/user_service.py
import logging
import os
from datetime import datetime, timedelta,timezone
from typing import Optional, Dict, Any
from dotenv import load_dotenv
load_dotenv()

import jwt

from app.config.settings import Settings
from app.core.database import Database
from app.models.user import User, UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        self.db = Database.get_db()
        self.user_model = User(self.db)

    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Create a new user and return user data with token."""
        try:
            user_id = await self.user_model.create_user(
                email=user_data.email,
                username=user_data.username,
                password=user_data.password,
                full_name=user_data.full_name
            )

            # Get created user (without password hash)
            user = await self.user_model.get_user_by_id(str(user_id))

            # Generate access token
            access_token = self.create_access_token(str(user_id))

            return {
                "user": user,
                "access_token": access_token
            }

        except ValueError as e:
            logger.warning(f"Validation error in create_user: {e}")
            print(f"Validation error in create_user: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in create_user: {e}")
            print(f"Error in create_user: {e}")

            raise

    async def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data with token."""
        try:
            user = await self.user_model.authenticate_user(email, password)
            if not user:
                return None

            # Generate access token
            access_token = self.create_access_token(str(user['_id']))

            return {
                "user": user,
                "access_token": access_token
            }

        except Exception as e:
            logger.error(f"Error in authenticate: {e}")
            raise

    def create_access_token(self, user_id: str) -> str:
        """Create a new access token."""
        try:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=60
            )
            to_encode = {
                "sub": user_id,
                "exp": expire
            }
            return jwt.encode(
                to_encode,
                os.getenv("SECRET_KEY"),
                algorithm="HS256"
            )
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise

    def verify_token(self, token: str) -> Optional[str]:
        """Verify token and return user_id if valid."""
        try:
            payload = jwt.decode(
                token,
                Settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return await self.user_model.get_user_by_id(user_id)

    async def update_user(
            self,
            user_id: str,
            update_data: UserUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update user information."""
        try:
            success = await self.user_model.update_user(user_id, update_data)
            if success:
                return await self.get_user(user_id)
            return None
        except ValueError as e:
            logger.warning(f"Validation error in update_user: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in update_user: {e}")
            raise

    async def change_password(
            self,
            user_id: str,
            current_password: str,
            new_password: str
    ) -> bool:
        """Change user password."""
        try:
            return await self.user_model.update_password(
                user_id,
                current_password,
                new_password
            )
        except ValueError as e:
            logger.warning(f"Validation error in change_password: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in change_password: {e}")
            raise


import asyncio

if __name__ == '__main__':
    async def main():
        await Database.connect()
        user_service = UserService()



        new_user = UserCreate(
            email="benji.ollomo@gmail.com",
            username="benollomo",
            password="Ben123",
            full_name="Ben Ollomo"
        )
        # await user_service.create_user(new_user)

        email = "benji.ollomo@gmail.com"
        password = "Ben123"
        loggin_info = await user_service.authenticate(email, password)
        print(loggin_info)

    # asyncio.run(main())
