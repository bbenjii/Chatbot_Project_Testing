"""
CUSTOM CLASS TO PERFORM OPERATIONS ON VECTOR STORE
- EMBED AND INSERT DATA
- CREATE SEARCH INDEX
- QUERY SEARCH
"""
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import List, Literal

from langchain_openai import AzureOpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import BSHTMLLoader, PyPDFLoader, WebBaseLoader
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from langchain_core.documents import Document
from pymongo.errors import DuplicateKeyError
from pymongo.operations import SearchIndexModel

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()  # Load environment variables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreController:
    def __init__(self, database_name=None, collection_name=None, search_index_name=None):
        """Initialize the vector store controller."""
        # Environment variables
        self.database_name = database_name or os.getenv("DB_NAME")
        self.collection_name = collection_name or os.getenv("QC_COLLECTION")
        self.search_index_name = search_index_name or os.getenv("SEARCH_INDEX_NAME")
        self.unique_index_name = "unique_source_text_index"

        # MongoDB setup
        self.client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi('1'))
        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]

        # Embeddings model
        self.embeddings_model = AzureOpenAIEmbeddings(
            azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
        )

        # Vector store
        self.vector_store = MongoDBAtlasVectorSearch(
            collection=self.collection,
            embedding=self.embeddings_model,
            index_name=self.search_index_name,
            relevance_score_fn="cosine"
        )

        # Ensure indices exist
        self.create_unique_index()
        self.create_vector_search_index()

    def vector_search(self, query: str, top_k: int = 3):
        """Perform vector search using the query."""
        try:
            results = self.vector_store.similarity_search(query, k=top_k)
            logger.info(f"Vector search completed. Results: {len(results)} documents found.")
            return results
        except Exception as e:
            logger.error(f"Error during vector search: {e}")
            return []

    def insert_data(self, sources: List[str], sources_type: Literal['html', 'url', 'pdf']):
        """Insert data into the vector store from various sources."""
        docs = []
        for source in sources:
            try:
                if sources_type == 'html':
                    data = self.extract_from_html_doc(source)
                elif sources_type == 'url':
                    data = self.extract_from_url(source)
                elif sources_type == 'pdf':
                    data = self.extract_from_pdf(source)
                else:
                    logger.warning(f"Unsupported source type: {sources_type}")
                    continue

                for doc in data:
                    doc.page_content = self.sanitize_text(doc.page_content)
                    text_splitter = SemanticChunker(
                        embeddings=self.embeddings_model,
                        breakpoint_threshold_amount=95
                    )
                    chunks = text_splitter.split_documents([doc])
                    meta_data = doc.metadata
                    self.add_docs_to_mongo(chunks, meta_data)
            except Exception as e:
                logger.error(f"Error processing source '{source}': {e}")

    def add_docs_to_mongo(self, docs: List[Document], meta_data: dict):
        """Add documents to the MongoDB vector store."""
        try:
            documents = [
                Document(
                    page_content=doc.page_content,
                    metadata={"chunk_id": i + 1, "upload_date": datetime.now(timezone.utc), **meta_data}
                )
                for i, doc in enumerate(docs)
            ]
            self.vector_store.add_documents(documents)
            logger.info(f"Successfully added {len(documents)} documents to the vector store.")
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate document skipped: {e}")
        except Exception as e:
            logger.error(f"Error adding documents to MongoDB: {e}")

    def extract_from_html_doc(self, file_path):
        """Extract text from HTML documents."""
        loader = BSHTMLLoader(file_path)
        return loader.load()

    def extract_from_url(self, url):
        """Extract text from web pages."""
        headers = {"User-Agent": os.getenv("USER_AGENT")}
        loader = WebBaseLoader(url, header_template=headers)
        return loader.load()

    def extract_from_pdf(self, file_path):
        """Extract text from PDF files."""
        loader = PyPDFLoader(file_path)
        return loader.load_and_split()

    def sanitize_text(self, text: str):
        """Clean and sanitize text content."""
        return text.replace("\r", "").replace("\t", "").replace("\n\n", "")

    def create_vector_search_index(self):
        """Create a vector search index in MongoDB."""
        if self.search_index_exists(self.search_index_name):
            logger.info(f"Search index '{self.search_index_name}' already exists.")
            return

        try:
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
                name=self.search_index_name
            )
            self.collection.create_search_index(model=search_index_model)
            logger.info(f"Search index '{self.search_index_name}' created successfully.")
        except Exception as e:
            logger.error(f"Error creating search index '{self.search_index_name}': {e}")

    def delete_all_documents(self):
        """Delete all documents from the collection."""
        try:
            result = self.collection.delete_many({})
            logger.info(f"Deleted {result.deleted_count} documents from the collection.")
        except Exception as e:
            logger.error(f"Error while deleting documents: {e}")

    def create_unique_index(self):
        """Create a unique index to prevent duplicate documents."""
        if self.unique_index_exists(self.unique_index_name):
            logger.info(f"Unique index '{self.unique_index_name}' already exists.")
            return

        try:
            self.collection.create_index(
                [("source", 1), ("text", 1)],
                unique=True,
                name=self.unique_index_name
            )
            logger.info(f"Unique index '{self.unique_index_name}' created successfully.")
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate key error: {e}")
        except Exception as e:
            logger.error(f"Error creating unique index: {e}")

    def search_index_exists(self, index_name: str):
        """Check if a search index exists."""
        return any(index.get("name") == index_name for index in self.collection.list_search_indexes())

    def unique_index_exists(self, index_name: str):
        """Check if a unique index exists."""
        return index_name in self.collection.index_information()
#
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
# one_piece_vectorstore = VectorStoreController(collection_name=one_piece_collection)
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
# QC_vectorstore = VectorStoreController()
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
# insert_qc()

#
# # one_piece_vectorstore.delete_all_documents()
#
# # QC_vectorstore.delete_all_documents()
# # QC_vectorstore.delete_all_documents()
# # QC_vectorstore.collection.drop_indexes()
#
# # onePiece_insert()
#
# # onepiece_search()
