"""
CUSTOM CLASS TO PERFORM OPERATIONS ON VECTOR STORE
- EMBED AND INSERT DATA
- CREATE SEARCH INDEX
- QUERY SEARCH
"""
import os
import re
import time

from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import List, Literal

# LangChain imports
from langchain_openai import AzureOpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import BSHTMLLoader, PyPDFLoader, WebBaseLoader
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from langchain_core.documents import Document
from pymongo.errors import DuplicateKeyError
from pymongo.operations import SearchIndexModel, IndexModel
from langchain_text_splitters import CharacterTextSplitter

# MongoDB and LangChain setup
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()  # Load .env variables

class vectorStore_controller:
    def __init__(self, database_name = os.getenv("DB_NAME"), collection_name = os.getenv("QC_COLLECTION"), search_index_name = os.getenv("SEARCH_INDEX_NAME")):
        """SET UP FOR THE VECTOR STORE"""

        # Set up MongoDB client and collection
        self.client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi('1'))
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.search_index_name = search_index_name
        self.unique_index_name = "unique_source_text_index"

        # Initialize the embeddings model
        self.embeddings_model = AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"))

        # Set up the vector store
        self.vector_store = MongoDBAtlasVectorSearch(
            collection=self.collection,
            embedding=self.embeddings_model,
            index_name=self.search_index_name,  # The name of the index you set up in MongoDB Atlas
            relevance_score_fn="cosine"  # or "euclidean", depending on your use case
        )

        self.create_unique_index()
        self.create_vector_search_index()


    # Perform vector search
    def vector_search(self, query: str, top_k: int = 3):
        """Perform vector search using the query."""

        try:
            # Perform similarity search in MongoDB Atlas vector store
            results = self.vector_store.similarity_search(query, k=top_k)
            return results
        except Exception as e:
            print(f"Error during vector search: {e}")
            return []

    def insert_data(self, sources: List[str], sources_type: Literal['html', 'url', 'pdf']):
        """Insert data into the vector store from various sources."""
        docs = []
        for source in sources:
            datas = []
            # extract data / text
            if sources_type == 'html':
                data = self.extract_from_html_doc(source)
            elif sources_type == 'url':
                data = self.extract_from_url(source)
            elif sources_type == 'pdf':
                print("Processing pdf")
                data = self.extract_from_pdf(source)
            else:
                print(f"Unsupported source type: {sources_type}")
                continue
            # Sanitize content
            for doc in data:
                doc.page_content = self.sanitize_text(doc.page_content)
                # text_splitter = CharacterTextSplitter.from_tiktoken_encoder(encoding_name="cl100k_base", chunk_size=1000,  chunk_overlap=200)
                text_splitter = SemanticChunker(AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")),breakpoint_threshold_amount=95)
                docs = text_splitter.split_documents([doc])
                # print(len(docs))
                # for doc in docs:
                #     print(doc)
                #     print("_________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________")

                meta_data = docs[0].metadata  # Assumed that metadata exists
                # Add documents to MongoDB
                try:
                    self.add_docs_to_mongo(docs, meta_data)
                except DuplicateKeyError as e:
                    print(f"Document already exists: {e}")
                except Exception as e:
                    print(f"Error inserting documents: {e}")


    # Function to add documents to MongoDB Atlas vector store
    def add_docs_to_mongo(self, docs, meta_data):
        """Add documents to MongoDB vector store."""
        documents = []
        for i, doc in enumerate(docs):
            documents.append(
                Document(page_content=doc.page_content, metadata={"chunk_id": i + 1, "upload_data":datetime.now(timezone.utc), **meta_data})
            )

        # Add documents to the vector store, which will handle embedding storage
        self.vector_store.add_documents(docs)
        print(f"Successfully added {len(docs)} documents to the vector store.")


    def extract_from_html_doc(self, file_path):
        loader = BSHTMLLoader(file_path)
        data = loader.load()
        return data

        # Sanitize content
        data[0].page_content = self.sanitize_text(data[0].page_content)
        text_splitter = SemanticChunker(
            AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")))
        docs = text_splitter.split_documents([data[0]])
        return docs

    def extract_from_url(self, url):
        headers = {"User-Agent": os.getenv("USER_AGENT") }
        loader = WebBaseLoader(url, header_template=headers)
        data = loader.load()
        return data

        # Sanitize content
        # data[0].page_content = self.sanitize_text(data[0].page_content)
        # text_splitter = SemanticChunker(AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")))
        # docs = text_splitter.split_documents([data[0]])
        # return docs

    def extract_from_pdf(self, file_path):
        loader = PyPDFLoader(file_path)
        data = loader.load_and_split()

        return data


    def sanitize_text(self, text):
        return text.replace("\r", "").replace("\t", "").replace("\n\n", "")


    def create_vector_search_index(self):
        """Create a vector search index in MongoDB Atlas."""

        try:
            # Check if the index already exists
            if self.search_index_exists(self.search_index_name):
                return

            # Create the index model, then create the search index
            search_index_model = SearchIndexModel(
                definition={
                    "fields": [
                        {
                            "type": "vector",
                            "path": "embedding",
                            "numDimensions": 1536,
                            "similarity": "cosine"
                        },
                    ]
                },
                name="vector_query_index",
                type="vectorSearch"
            )

            # Create the index
            self.collection.create_search_index(model=search_index_model)

            print(f"Successfully created search index '{self.search_index_name}'.")
            return


        except Exception as e:
            print(f"Error creating search index: {e}")


    def delete_all_documents(self):
        try:
            # Delete all documents from the collection
            result = self.collection.delete_many({})
            print(f"Deleted {result.deleted_count} documents from the collection.")
        except Exception as e:
            print(f"Error while deleting documents: {e}")

    def create_unique_index(self):
        """Create a unique index on 'source' and 'page_content' to prevent duplicates."""
        try:
            if self.unique_index_exists(self.unique_index_name):
                return

            self.collection.create_index(
                [("source", 1), ("text", 1)],
                unique=True,
                name=self.unique_index_name
            )
            print("Unique index on 'source' and 'text' created successfully.")
        except DuplicateKeyError as e:
            print(f"Duplicate key error: {e}")
        except Exception as e:
            print(f"Error creating unique index: {e}")

    def search_index_exists(self, index_name: str):
        exists = False

        for index in self.collection.list_search_indexes():
            if index_name in index.values():
                exists = True

        return exists

    def unique_index_exists(self, index_name: str):
        return index_name in self.collection.index_information()

#
# QC_vectorstore = vectorStore_controller()
#
#
# directory = "../Test-Documents/qc-life-documents/"
# files_paths = []
# # Make list of all files in the directory
# for filename in os.listdir(directory):
#     if filename.endswith(".html"):  # You can specify any file extension here
#         file_path = os.path.join(directory, filename)
#         # print(f"Processing file: {file_path}")
#         files_paths.append(file_path)
#
#
# one_piece_collection = "One-Piece-KB_2"
# one_piece_vectorstore = vectorStore_controller(collection_name=one_piece_collection)
#
# def onePiece_insert():
#     one_piece_chapter_links = [
#         "https://onepiece.fandom.com/wiki/Chapter_1",
#         "https://onepiece.fandom.com/wiki/Chapter_2",
#         "https://onepiece.fandom.com/wiki/Chapter_3",
#         "https://onepiece.fandom.com/wiki/Chapter_4",
#         "https://onepiece.fandom.com/wiki/Chapter_5",
#         "https://onepiece.fandom.com/wiki/Chapter_6",
#         "https://onepiece.fandom.com/wiki/Chapter_7",
#         "https://onepiece.fandom.com/wiki/Chapter_8",
#         "https://onepiece.fandom.com/wiki/Chapter_9",
#         "https://onepiece.fandom.com/wiki/Chapter_10",
#     ]
#
#     wano_pdf = ["../../Test-Documents/one_piece_kb/wano_guide.pdf"]
#
#
#     # one_piece_vectorstore.insert_data(wano_pdf, "pdf")
#     one_piece_vectorstore.insert_data(one_piece_chapter_links, "url")
#     one_piece_vectorstore.insert_data(["https://onepiece.fandom.com/wiki/One_Piece_novel_A"], "url")
#
#
# def onepiece_search():
#     results = one_piece_vectorstore.vector_search("Who is Monkey D Luffy?", top_k=10)
#     # print(results)
#     # for result in results:
#         # print(result.page_content)
#         # print(str(result.metadata))
#         # print("____________________________________________________________________________________________________")
#
#
#
# def insert_qc():
#     qc_links = [
#         "https://qclife.ca/contact-us/",
#         "https://qclife.ca/",
#         "https://qclife.ca/about/",
#         "https://qclife.ca/faq/",
#         "https://qclife.ca/terms-of-use/",
#         "https://qclife.ca/privacy-policy/",
#     ]
#
#     QC_vectorstore.insert_data(qc_links, "url")
#
#
# # one_piece_vectorstore.delete_all_documents()
#
# # insert_qc()
# # QC_vectorstore.delete_all_documents()
# # QC_vectorstore.delete_all_documents()
# # QC_vectorstore.collection.drop_indexes()
#
# # onePiece_insert()
#
# # onepiece_search()
