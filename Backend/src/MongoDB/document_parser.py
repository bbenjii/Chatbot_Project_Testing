"""
WEBSITE TEXT EXTRACTOR
"""
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import requests
from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
import random
from langchain_text_splitters import CharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
from openai import azure_endpoint, embeddings
from langchain_community.document_loaders import BSHTMLLoader
import asyncio

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os


load_dotenv() #load .env variables


# Initialize MongoDB client
client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi('1'))

db = client["Chatbot-Test"]
collection = db["QC_Life_Docs"]


def extract_from_url(url):
    headers = {
        "User-Agent": os.getenv("USER_AGENT")
    }
    # load webpage data
    loader = WebBaseLoader(url, header_template=headers)
    data = loader.load()

    # sanitation
    # remove spaces and space breaks
    data[0].page_content = data[0].page_content.replace("\n\n","").replace("  ","").replace("\t","")

    text_splitter = SemanticChunker(AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")))

    docs = text_splitter.split_documents([data[0]])

    return docs


def extract_from_html_doc(file_path):
    file_path = file_path

    # load webpage data
    loader = BSHTMLLoader(file_path)
    data = loader.load()

    # extract page content and meta data
    meta_data = data[0].metadata

    # remove spaces and space breaks
    data[0].page_content = data[0].page_content.replace("\n\n","").replace("  ","").replace("\t", "")

    text_splitter = SemanticChunker(AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")))

    docs = text_splitter.split_documents([data[0]])

    print("----Text Extraction Finished---")
    return docs


def embed_docs(docs):
    embeddings_model = AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"))
    chunks = []
    for i in range(len(docs)):
        chunks.append({
            "chunk_id": i+1,
            "chunk_content": docs[i].page_content,
            "chunk_embedding": embeddings_model.embed_documents([docs[i].page_content])[0]
        })

    print("----Chunks Embedding Finished----")
    return chunks


def mongo_insert(chunks, meta_data):
    mongo_document = {
        "file_name": meta_data.get("title", "unknown"),
        "source": meta_data.get("source", "unknown"),
        "upload_date": datetime.now(timezone.utc),
        "content_type": meta_data.get("content_type", None),  # You can adjust this based on the document type
        "chunks": [chunks],
        "metadata": meta_data
    }

    # Insert the document into MongoDB
    collection.insert_one(mongo_document)
    print(f"Document {mongo_document['file_name']} inserted successfully")


def upload_files(files_paths : [str]):
    for file_path in files_paths:
        docs = []
        docs = extract_from_html_doc(file_path)
        chunks = embed_docs(docs)
        meta_data = docs[0].metadata
        mongo_insert(chunks, meta_data)

def upload_url_contents(urls : [str]):
    for url in urls:
        docs = (extract_from_url(url)) # list of documents {page_content: "", metadata: ""}
        chunks = embed_docs(docs)
        print(len(chunks[0].get("chunk_embedding")))
        meta_data = docs[0].metadata

        mongo_insert(chunks, meta_data)


""" Inserting One Url Content """
urls = []

urls.append("https://qclife.ca/")
upload_url_contents(urls)


"""  insert multiple docs. """

# Specify the directory path
directory = "../../Test-Documents/qc-life-documents/"
files_paths = []
# make list of all files in directory
# for filename in os.listdir(directory):
#     if filename.endswith(".html"):  # You can specify any file extension here
#         file_path = os.path.join(directory, filename)
#         print(f"Processing file: {file_path}")
#         # Add your file processing logic here
#         files_paths.append(file_path)
#
#
# upload_files(files_paths)
