import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# LangChain imports
from langchain_community.document_loaders import WebBaseLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import BSHTMLLoader
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from langchain_core.documents import Document

# MongoDB and LangChain setup
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()  # Load .env variables

# Initialize MongoDB client for Atlas
MONGODB_ATLAS_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_ATLAS_URI, server_api=ServerApi('1'))
db_name = "Chatbot-Test"
db = client[db_name]
collection_name = "QC_Life_Docs"
collection = db[collection_name]

# Setup for MongoDB Atlas Vector Search
embeddings_model = AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"))

# Initialize the MongoDB Atlas Vector Store for the collection
vector_store = MongoDBAtlasVectorSearch(
    collection=collection,
    embedding=embeddings_model,
    index_name="qc_life_vector_search",  # The name of the index you set up in MongoDB Atlas
    relevance_score_fn="cosine"  # or "euclidean", depending on your use case
)



# Function to extract text from URL
def extract_from_url(url):
    headers = {
        "User-Agent": os.getenv("USER_AGENT")
    }
    loader = WebBaseLoader(url, header_template=headers)
    data = loader.load()

    # Sanitize and process content
    data[0].page_content = data[0].page_content.replace("\r", "\n").replace("\n\n", "").replace("  ", "").replace("\t", "").replace("\n \n", "")

    text_splitter = SemanticChunker(AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")))
    docs = text_splitter.split_documents([data[0]])

    return docs


# Function to extract text from HTML document
def extract_from_html_doc(file_path):
    loader = BSHTMLLoader(file_path)
    data = loader.load()

    # Sanitize content
    data[0].page_content = data[0].page_content.replace("\r", "\n").replace("\n\n", "").replace("  ", "").replace("\t", "").replace("\n \n", "")
    text_splitter = SemanticChunker(AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")))
    docs = text_splitter.split_documents([data[0]])
    print(docs)
    for doc in docs:
        print(doc.page_content)
    print("------TEXT EXTRACTION COMPLETE------")
    print("------TEXT EXTRACTION COMPLETE------")
    return docs


# Function to add documents to MongoDB Atlas vector store
def add_docs_to_mongo(docs, meta_data):
    documents = []
    for i, doc in enumerate(docs):
        documents.append(
            Document(page_content=doc.page_content, metadata={"chunk_id": i + 1, **meta_data})
        )
    print(f"Uploading {len(docs)} documents to the {collection_name} collection...")

    # Add documents to the vector store, which will handle embedding storage
    vector_store.add_documents(documents)
    print(f"Documents added to vector store with metadata: {meta_data}")


# Function to upload files to MongoDB
def upload_files(files_paths):
    for file_path in files_paths:
        docs = extract_from_html_doc(file_path)
        meta_data = docs[0].metadata  # Assumed that metadata exists
        add_docs_to_mongo(docs, meta_data)


# Function to upload URL contents
def upload_url_contents(urls):
    for url in urls:
        docs = extract_from_url(url)
        meta_data = docs[0].metadata  # Assumed that metadata exists
        add_docs_to_mongo(docs, meta_data)


""" Inserting one URL content """
urls = ["https://qclife.ca/"]
# upload_url_contents(urls)

""" Insert multiple docs """
# Specify the directory path
directory = "../../Test-Documents/qc-life-documents/"
files_paths = []

# Make list of all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".html"):  # You can specify any file extension here
        file_path = os.path.join(directory, filename)
        print(f"Processing file: {file_path}")
        files_paths.append(file_path)

upload_files(files_paths)
