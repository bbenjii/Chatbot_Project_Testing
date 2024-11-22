import os
import logging
import uuid
from datetime import datetime, timedelta, timezone
import mimetypes

from aiohttp.web_fileresponse import content_type
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings

load_dotenv()

logging.getLogger("azure").setLevel(logging.WARNING)

class AzureStorageController:
    def __init__(self):
        self.account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.account_url = os.getenv("AZURE_STORE_ACCOUNT_URL")
        self.container_name = "chatbot-storage"

        self.default_credential = DefaultAzureCredential()
        self.blob_service_client = BlobServiceClient(self.account_url, credential=self.default_credential)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def add_file(self, file_content, blob_name, content_type):
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            content_settings = ContentSettings(content_type=content_type)

            # Upload the file content
            blob_client.upload_blob(file_content, content_settings=content_settings, overwrite=True)
            self.logger.info(f"File uploaded as blob '{blob_name}' successfully.")
            return blob_client.url

        except Exception as ex:
            self.logger.error(f"Error uploading file: {ex}")
            raise  # Re-raise the exception to be caught by the calling function

    def add_loca_file(self, file_path, blob_name):
        try:
            # Determine content type based on file extension
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"  # Default content type if unknown

            blob_client = self.container_client.get_blob_client(blob_name)
            content_settings = ContentSettings(content_type=content_type)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, content_settings=content_settings, overwrite=True)
                self.logger.info(f"File '{file_path}' uploaded as blob '{blob_name}' successfully.")
            return blob_client.url
        except Exception as ex:
            self.logger.error(f"Error uploading file '{file_path}': {ex}")

    def list_files_names(self):
        try:
            blob_list = self.container_client.list_blobs()
            for blob in blob_list:
                print(f"- {blob.name}")

            return blob_list
        except Exception as ex:
            self.logger.error(f"Error listing files: {ex}")

    def get_blob_url_with_sas(self, blob_name):
        sas_token = generate_blob_sas(
            account_name=self.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=os.getenv("AZURE_STORAGE_ACCESS_KEY"),
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=1)  # Expires in 1 hour
        )
        return f"{self.account_url}/{self.container_name}/{blob_name}?{sas_token}"

    def list_files_with_urls(self):
        try:
            blob_list = self.container_client.list_blobs()
            blob_urls = []
            for blob in blob_list:
                # print(blob)
                blob_name = blob.get("name")
                blob_content_type = blob.get("content_settings").get("content_type")
                blob_urls.append({"name":blob_name, "url": self.get_blob_url_with_sas(blob_name), "content_type":blob_content_type})
            #
            # blob_urls = [f"{self.account_url}/{self.container_name}/{blob.name}" for blob in blob_list]
            return blob_urls
        except Exception as ex:
            self.logger.error(f"Error listing files: {ex}")

    def delete_file(self, blob_name):
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob(delete_snapshots='include')
            self.logger.info(f"Blob '{blob_name}' deleted successfully.")
        except Exception as ex:
            self.logger.error(f"Error deleting blob '{blob_name}': {ex}")

    def generate_blob_name(self, original_name):
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex
        extension = os.path.splitext(original_name)[0]
        # return f"{extension}"

        return f"{timestamp}_{unique_id}{extension}"

    def generate_sas_token(self, blob_name, expiry_hours=1):
        try:
            sas_token = generate_blob_sas(
                account_name=self.account_url.split("//")[1].split(".")[0],
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=os.getenv("AZURE_STORAGE_ACCOUNT_KEY"),
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            return f"{self.account_url}/{self.container_name}/{blob_name}?{sas_token}"
        except Exception as ex:
            self.logger.error(f"Error generating SAS token for '{blob_name}': {ex}")


cv_path = "../../Test-Documents/ben-resumes/benollomo-cv.pdf"
cover_letter_path = "../../Test-Documents/ben-resumes/benollomo-cover-letter.pdf"
goku_1_path = "../../Test-Documents/images/picolo.jpeg"

# download_path = "../../Test-Documents/ben-resumes/blob_download.pdf"
#
#
storage = AzureStorageController()

# add File
# storage.add_loca_file(goku_1_path, "Picolo")
# storage.add_loca_file(cover_letter_path, "benollomo-cover-letter")

# storage.delete_file("benollomo-cv")
# storage.delete_file("benollomo-cv.pdf")
# storage.delete_file("blob_name")

# download file
# storage.download_file("blob_name", download_path)
# List Blobs
# print(storage.list_files_with_urls())
# print(storage.get_blob_url_with_sas("benollomo-cv"))
# storage.list_files_names()

# print(storage.generate_blob_name("benjamin"))

# Determine content type based on file extension
# content_type, _ = mimetypes.guess_type(goku_1_path)
# if not content_type:
#     content_type = "application/octet-stream"  # Default content type if unknown
# print(content_type)