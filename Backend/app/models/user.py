# app/models/user.py
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field
from app.models.base import BaseModel as MongoBaseModel
import bcrypt
import logging

logger = logging.getLogger(__name__)

# Pydantic models for validation
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "strongpassword123",
                "full_name": "John Doe"
            }
        }


class UserUpdate(BaseModel):
    email: Optional[EmailStr]
    username: Optional[str]
    full_name: Optional[str]
    settings: Optional[Dict[str, Any]]


class UserInDB(BaseModel):
    id: str = Field(alias='_id')
    email: EmailStr
    username: str
    full_name: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    settings: Dict[str, Any]

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class User(MongoBaseModel):
    collection_name = 'users'

    @staticmethod
    def hash_password(password: str) -> bytes:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: bytes) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

    async def create_user(
            self,
            email: str,
            username: str,
            password: str,
            full_name: Optional[str] = None,
            settings: Optional[Dict[str, Any]] = None
    ) -> ObjectId:
        """Create a new user."""
        try:
            # Check if user already exists
            if await self.find_one({'email': email}):
                raise ValueError("Email already registered")
            if await self.find_one({'username': username}):
                raise ValueError("Username already taken")

            # Prepare user document
            user_doc = {
                'email': email,
                'username': username,
                'password_hash': self.hash_password(password),
                'full_name': full_name,
                'created_at': datetime.utcnow(),
                'last_login': None,
                'is_active': True,
                'settings.py': settings or {
                    'theme': 'light',
                    'language': 'en',
                    'notifications_enabled': True
                },
                'email_verified': False,
                'verification_token': None
            }

            # Insert user
            user_id = await self.insert_one(user_doc)
            logger.info(f"Created new user with ID: {user_id}")
            print(f"Created new user with ID: {user_id}")
            return user_id

        except Exception as e:
            logger.error(f"Error creating user: {e}")
            print(f"Error creating user: {e}")
            raise

    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user by email and password."""
        try:
            user = await self.find_one({'email': email, 'is_active': True})
            if not user:
                return None

            if not self.verify_password(password, user['password_hash']):
                return None

            # Update last login
            await self.update_one(
                {'_id': user['_id']},
                {'last_login': datetime.utcnow()}
            )

            # Remove sensitive data
            user.pop('password_hash', None)
            return user

        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            print(f"Error authenticating user: {e}")
            raise

    async def update_user(
            self,
            user_id: str,
            update_data: UserUpdate
    ) -> bool:
        """Update user information."""
        try:
            # Convert to dict and remove None values
            update_dict = update_data.dict(exclude_unset=True)

            if not update_dict:
                return False

            # Check email uniqueness if email is being updated
            if 'email' in update_dict:
                existing = await self.find_one({
                    'email': update_dict['email'],
                    '_id': {'$ne': ObjectId(user_id)}
                })
                if existing:
                    raise ValueError("Email already registered")

            # Check username uniqueness if username is being updated
            if 'username' in update_dict:
                existing = await self.find_one({
                    'username': update_dict['username'],
                    '_id': {'$ne': ObjectId(user_id)}
                })
                if existing:
                    raise ValueError("Username already taken")

            result = await self.update_one(
                {'_id': ObjectId(user_id)},
                update_dict
            )
            return result

        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            user = await self.find_one({'_id': ObjectId(user_id)})
            if user:
                user.pop('password_hash', None)
            return user
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            print(f"Error fetching user: {e}")
            raise

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account."""
        try:
            result = await self.update_one(
                {'_id': ObjectId(user_id)},
                {'is_active': False}
            )
            return result
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            print(f"Error deactivating user: {e}")
            raise

    async def update_password(
            self,
            user_id: str,
            current_password: str,
            new_password: str
    ) -> bool:
        """Update user password."""
        try:
            user = await self.find_one({'_id': ObjectId(user_id)})
            if not user:
                return False

            # Verify current password
            if not self.verify_password(current_password, user['password_hash']):
                raise ValueError("Current password is incorrect")

            # Update to new password
            result = await self.update_one(
                {'_id': ObjectId(user_id)},
                {'password_hash': self.hash_password(new_password)}
            )
            return result

        except Exception as e:
            logger.error(f"Error updating password: {e}")
            raise