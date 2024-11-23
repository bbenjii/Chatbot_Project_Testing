# app/core/azure_storage.py
from typing import List, Dict, Any, Optional
import os
import logging
import uuid
from datetime import datetime, timedelta, timezone
import mimetypes
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from app.core.exceptions import AppException

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class AzureStorageClient:
    """Core Azure Storage client for blob operations."""

    def __init__(self):
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_url = os.getenv("AZURE_STORE_ACCOUNT_URL")
        self.account_key = os.getenv("AZURE_STORAGE_ACCESS_KEY")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "chatbot-storage")

        try:
            # Initialize Azure clients
            self.default_credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(
                self.account_url, credential=self.default_credential)
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            # Verify connection
            self.container_client.get_container_properties()
            logger.info("Successfully connected to Azure Storage")

        except Exception as e:
            logger.error(f"Failed to initialize Azure Storage client: {e}")
            raise AppException(f"Storage initialization failed: {str(e)}")

    async def upload_blob(
            self,
            file_content: bytes,
            blob_name: str,
            content_type: Optional[str] = None,
            metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload a blob to Azure Storage."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)

            # Set content settings
            content_settings = ContentSettings(
                content_type=content_type or "application/octet-stream"
            )

            # Upload the file
            blob_client.upload_blob(
                file_content,
                content_settings=content_settings,
                metadata=metadata,
                overwrite=True
            )

            logger.info(f"Successfully uploaded blob: {blob_name}")

            # Generate SAS URL for immediate access
            return await self.get_blob_url_with_sas(blob_name)

        except Exception as e:
            logger.error(f"Error uploading blob {blob_name}: {e}")
            raise AppException(f"Failed to upload file: {str(e)}")

    async def download_blob(self, blob_name: str) -> bytes:
        """Download a blob's content."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            return await download_stream.readall()

        except Exception as e:
            logger.error(f"Error downloading blob {blob_name}: {e}")
            raise AppException(f"Failed to download file: {str(e)}")

    async def delete_blob(self, blob_name: str) -> bool:
        """Delete a blob."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob(delete_snapshots='include')
            logger.info(f"Successfully deleted blob: {blob_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting blob {blob_name}: {e}")
            raise AppException(f"Failed to delete file: {str(e)}")

    async def get_blob_url_with_sas(
            self,
            blob_name: str,
            expiry_hours: int = 1
    ) -> str:
        """Generate a SAS URL for blob access."""
        try:
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
            )

            # Construct full URL
            return f"{self.account_url}/{self.container_name}/{blob_name}?{sas_token}"

        except Exception as e:
            logger.error(f"Error generating SAS URL for {blob_name}: {e}")
            raise AppException(f"Failed to generate access URL: {str(e)}")

    async def list_blobs(
            self,
            name_starts_with: Optional[str] = None,
            include_metadata: bool = False
    ) -> List[Dict[str, Any]]:
        """List blobs in the container."""
        try:
            blobs = []
            async for blob in self.container_client.list_blobs(
                    name_starts_with=name_starts_with
            ):
                blob_info = {
                    "name": blob.name,
                    "size": blob.size,
                    "content_type": blob.content_settings.content_type,
                    "created_at": blob.creation_time,
                    "last_modified": blob.last_modified
                }

                if include_metadata:
                    blob_info["metadata"] = blob.metadata
                    blob_info["url"] = await self.get_blob_url_with_sas(blob.name)

                blobs.append(blob_info)

            return blobs

        except Exception as e:
            logger.error(f"Error listing blobs: {e}")
            raise AppException(f"Failed to list files: {str(e)}")

    def generate_blob_name(
            self,
            original_name: str,
            user_id: Optional[str] = None
    ) -> str:
        """Generate a unique blob name."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        name = f"{user_id}/{original_name}_{timestamp}"
        return name

    async def copy_blob(
            self,
            source_blob_name: str,
            destination_blob_name: str
    ) -> bool:
        """Copy a blob within the same container."""
        try:
            source_blob = self.container_client.get_blob_client(source_blob_name)
            dest_blob = self.container_client.get_blob_client(destination_blob_name)

            # Get source URL with SAS token
            source_url = await self.get_blob_url_with_sas(source_blob_name)

            # Start copy operation
            copy = await dest_blob.start_copy_from_url(source_url)

            logger.info(
                f"Successfully copied blob from {source_blob_name} "
                f"to {destination_blob_name}"
            )
            return True

        except Exception as e:
            logger.error(f"Error copying blob: {e}")
            raise AppException(f"Failed to copy file: {str(e)}")

    async def get_blob_metadata(self, blob_name: str) -> Dict[str, Any]:
        """Get blob metadata and properties."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            properties = blob_client.get_blob_properties()

            return {
                "name": blob_name,
                "size": properties.size,
                "content_type": properties.content_settings.content_type,
                "created_at": properties.creation_time,
                "last_modified": properties.last_modified,
                "metadata": properties.metadata,
                "lease_state": properties.lease.state
            }

        except Exception as e:
            logger.error(f"Error getting blob metadata {blob_name}: {e}")
            raise AppException(f"Failed to get file metadata: {str(e)}")

    async def update_blob_metadata(
            self,
            blob_name: str,
            metadata: Dict[str, str]
    ) -> bool:
        """Update blob metadata."""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.set_blob_metadata(metadata=metadata)
            logger.info(f"Updated metadata for blob: {blob_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating blob metadata {blob_name}: {e}")
            raise AppException(f"Failed to update file metadata: {str(e)}")


    async def add_local_file(self, file_path, blob_name):
        try:
            # Determine content type based on file extension
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"  # Default content type if unknown

            blob_client = self.container_client.get_blob_client(blob_name)
            content_settings = ContentSettings(content_type=content_type)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, content_settings=content_settings, overwrite=True)
                logger.info(f"File '{file_path}' uploaded as blob '{blob_name}' successfully.")
            return blob_client.url
        except Exception as ex:
            logger.error(f"Error uploading file '{file_path}': {ex}")

import asyncio

if __name__ == '__main__':
    async def main():
        cv_path = "../../Test-Documents/ben-resumes/benollomo-cv.pdf"
        cover_letter_path = "../../Test-Documents/ben-resumes/benollomo-cover-letter.pdf"
        goku_1_path = "../../Test-Documents/images/picolo.jpeg"

        client = AzureStorageClient()

        file = None
        with open(cover_letter_path, "rb") as data:
            file = data.read()


        # add file
        # await client.upload_blob(file, "cover-letter", "application/pdf")
        # print(client.generate_blob_name("cover-letter", "benollomo"))
        # await client.delete_blob("cover-letter")
    asyncio.run(main())