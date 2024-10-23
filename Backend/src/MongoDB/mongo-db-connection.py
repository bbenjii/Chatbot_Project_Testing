"""
Code Showing how to set up MongoDB connection
"""
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

from dotenv import load_dotenv
load_dotenv() #load .env variables

# Create a new client and connect to the server
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri, server_api=ServerApi('1'))


# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)