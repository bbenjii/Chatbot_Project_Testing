"""
CUSTOM CLASS TO PERFORM OPERATIONS ON VECTOR STORE
- EMBED AND INSERT DATA
- CREATE SEARCH INDEX
- QUERY SEARCH
"""
import os
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
from pymongo.operations import SearchIndexModel
from langchain_text_splitters import CharacterTextSplitter

# MongoDB and LangChain setup
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()  # Load .env variables

class MongoDBVectorStore:
    def __init__(self, database_name = os.getenv("DB_NAME"), collection_name = os.getenv("QC_COLLECTION"), search_index_name = os.getenv("SEARCH_INDEX_NAME")):
        """SET UP FOR THE VECTOR STORE"""
        self.client = MongoClient(os.getenv("MONGODB_URI"), server_api=ServerApi('1'))

        #Connect to DB
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

        # Setup for MongoDB Atlas Vector Search
        self.embeddings_model = AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"))

        self.search_index_name = search_index_name
        self.vector_store = MongoDBAtlasVectorSearch(
            collection=self.collection,
            embedding=self.embeddings_model,
            index_name=self.search_index_name,  # The name of the index you set up in MongoDB Atlas
            relevance_score_fn="cosine"  # or "euclidean", depending on your use case
        )

        self.create_unique_index()


    # Perform vector search
    def vector_search(self, query, top_k=3):
        # Generate embedding for the query using the same embedding model
        query_embedding = self.embeddings_model.embed_documents([query])[0]

        # self.create_vector_search_index()
        try:
            # Perform similarity search in MongoDB Atlas vector store
            results = self.vector_store.similarity_search(query, k=top_k)

            return results
        except Exception as e:
            print(e)



    def insert_data(self, sources: List[str], sources_types: List[Literal['html', 'url', 'pdf']]):
        docs = []
        # data = [Document(page_content="")]
        for source in sources:
            # extract data / text
            if sources_types == 'html':
                datas = self.extract_from_html_doc(source)
            elif sources_types == 'url':
                datas = self.extract_from_url(source)
            elif sources_types == 'pdf':
                print("Processing pdf")
                datas = self.extract_from_pdf(source)

            # Sanitize content
            for data in datas:
                data.page_content = self.sanitize_text(data.page_content)
                # text_splitter = CharacterTextSplitter.from_tiktoken_encoder(encoding_name="cl100k_base", chunk_size=600,  chunk_overlap=50)
                text_splitter = SemanticChunker(AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")))
                docs = text_splitter.split_documents([data])

                # for doc in docs:
                #     print(doc)

                meta_data = docs[0].metadata  # Assumed that metadata exists
                try:
                    self.add_docs_to_mongo(docs, meta_data)
                except Exception as e:
                    if e.code == 11000:
                        print(f"Doc already exists: {e}")
                    else:
                        print(f"Error insesrting doc: {e}")


    # Function to add documents to MongoDB Atlas vector store
    def add_docs_to_mongo(self, docs, meta_data):
        documents = []
        for i, doc in enumerate(docs):
            documents.append(
                Document(page_content=doc.page_content, metadata={"chunk_id": i + 1, "upload_data":datetime.now(timezone.utc), **meta_data})
            )

        # Add documents to the vector store, which will handle embedding storage
        try:
            self.vector_store.add_documents(documents)
            print(f"Sucess. Documents added to vector store with metadata: {meta_data}")
        except Exception as e:
            if e.code == 11000:
                print(f"Doc already exists: {e}")
            else:
                print(e[0])
                print(f"Error inserting doc: {e}")
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
        return text.replace("\r", "\n").replace("\n\n", "").replace("  ", "").replace("\t", "").replace("\n \n", "")


    def create_vector_search_index(self):
        indexes = self.collection.list_indexes()
        # return
        if self.search_index_name not in indexes:
            while True:
                try:
                    # Define the vector search index
                    index = {
                        "name": self.search_index_name,  # The index name
                        "type": "vectorSearch",
                        "definition": {
                            "fields": [
                                {
                                    "type": "vector",
                                    "numDimensions": 1536,
                                    # Adjust this to match the dimensionality of your embeddings (e.g., OpenAI embeddings have 1536 dimensions)
                                    "path": "embedding",  # Path to the vector field in your documents
                                    "similarity": "cosine"  # Similarity metric (can be "cosine", "euclidean", or "dotProduct")
                                }
                            ]
                        }
                    }
                    # Create your index model, then create the search index
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

                    result = self.collection.create_search_index(model=search_index_model)

                    print(f"Sucess: Creating Index: {result}")
                    return

                except Exception as e:
                    if e.code == 68:
                        print(f"Success: Search Index Found.")
                        return
                    else:
                        print(f"Error: Index creation still in progress...: {e.details}...")
                        time.sleep(2)
        else:
            return

    def delete_all_documents(self):
        try:
            # Delete all documents from the collection
            result = self.collection.delete_many({})
            print(f"Deleted {result.deleted_count} documents from the collection.")
        except Exception as e:
            print(f"Error while deleting documents: {e}")

    def create_unique_index(self):
        try:
            # Create a unique index on 'title' and 'source' to prevent duplicates
            self.collection.create_index([("source", 1), ("text", 1)], unique=True)
            print("Unique index on 'source' and 'text' created successfully.")
        except Exception as e:
            if e.code == 11000:
                raise
            else:
                print(f"Error creating unique index: {e}")

QC_vectorstore = MongoDBVectorStore()
# QC_vectorstore.delete_all_documents()

directory = "../../Test-Documents/qc-life-documents/"
files_paths = []

# Make list of all files in the directory
# for filename in os.listdir(directory):
#     if filename.endswith(".html"):  # You can specify any file extension here
#         file_path = os.path.join(directory, filename)
#         print(f"Processing file: {file_path}")
#         files_paths.append(file_path)

# QC_vectorstore.insert_data(files_paths, "html")
# results = (QC_vectorstore.vector_search("How can I contact someone?"))
# for result in results:
#     print(result.page_content)
#     print(result.metadata)
#     print("___________")

one_piece_collection = "One-Piece-KB"
one_piece_vectorstore = MongoDBVectorStore(collection_name=one_piece_collection)
one_piece_chapter_links = [
    "https://onepiece.fandom.com/wiki/Chapter_1",
    "https://onepiece.fandom.com/wiki/Chapter_2",
    "https://onepiece.fandom.com/wiki/Chapter_3",
    "https://onepiece.fandom.com/wiki/Chapter_4",
    "https://onepiece.fandom.com/wiki/Chapter_5",
    "https://onepiece.fandom.com/wiki/Chapter_6",
    "https://onepiece.fandom.com/wiki/Chapter_7",
    "https://onepiece.fandom.com/wiki/Chapter_8",
    "https://onepiece.fandom.com/wiki/Chapter_9",
    "https://onepiece.fandom.com/wiki/Chapter_10",
    # "https://onepiece.fandom.com/wiki/Chapter_11",
    # "https://onepiece.fandom.com/wiki/Chapter_12",
    # "https://onepiece.fandom.com/wiki/Chapter_13",
    # "https://onepiece.fandom.com/wiki/Chapter_14",
    # "https://onepiece.fandom.com/wiki/Chapter_15",
    # "https://onepiece.fandom.com/wiki/Chapter_16",
    # "https://onepiece.fandom.com/wiki/Chapter_17",
    # "https://onepiece.fandom.com/wiki/Chapter_18",
    # "https://onepiece.fandom.com/wiki/Chapter_19",
    # "https://onepiece.fandom.com/wiki/Chapter_20",
    # "https://onepiece.fandom.com/wiki/Chapter_21",
    # "https://onepiece.fandom.com/wiki/Chapter_22",
    # "https://onepiece.fandom.com/wiki/Chapter_23",
    # "https://onepiece.fandom.com/wiki/Chapter_24",
    # "https://onepiece.fandom.com/wiki/Chapter_25",
    # "https://onepiece.fandom.com/wiki/Chapter_26",
    # "https://onepiece.fandom.com/wiki/Chapter_27",
    # "https://onepiece.fandom.com/wiki/Chapter_28",
    # "https://onepiece.fandom.com/wiki/Chapter_29",
    # "https://onepiece.fandom.com/wiki/Chapter_30",
    # "https://onepiece.fandom.com/wiki/Chapter_31",
    # "https://onepiece.fandom.com/wiki/Chapter_32",
    # "https://onepiece.fandom.com/wiki/Chapter_33",
    # "https://onepiece.fandom.com/wiki/Chapter_34",
    # "https://onepiece.fandom.com/wiki/Chapter_35",
    # "https://onepiece.fandom.com/wiki/Chapter_36",
    # "https://onepiece.fandom.com/wiki/Chapter_37",
    # "https://onepiece.fandom.com/wiki/Chapter_38",
    # "https://onepiece.fandom.com/wiki/Chapter_39",
    # "https://onepiece.fandom.com/wiki/Chapter_40",
    # "https://onepiece.fandom.com/wiki/Chapter_41",
    # "https://onepiece.fandom.com/wiki/Chapter_42",
    # "https://onepiece.fandom.com/wiki/Chapter_43",
    # "https://onepiece.fandom.com/wiki/Chapter_44",
    # "https://onepiece.fandom.com/wiki/Chapter_45",
    # "https://onepiece.fandom.com/wiki/Chapter_46",
    # "https://onepiece.fandom.com/wiki/Chapter_47",
    # "https://onepiece.fandom.com/wiki/Chapter_48",
    # "https://onepiece.fandom.com/wiki/Chapter_49",
    # "https://onepiece.fandom.com/wiki/Chapter_50",
    # "https://onepiece.fandom.com/wiki/Chapter_51",
    # "https://onepiece.fandom.com/wiki/Chapter_52",
    # "https://onepiece.fandom.com/wiki/Chapter_53",
    # "https://onepiece.fandom.com/wiki/Chapter_54",
    # "https://onepiece.fandom.com/wiki/Chapter_55",
    # "https://onepiece.fandom.com/wiki/Chapter_56",
    # "https://onepiece.fandom.com/wiki/Chapter_57",
    # "https://onepiece.fandom.com/wiki/Chapter_58",
    # "https://onepiece.fandom.com/wiki/Chapter_59",
    # "https://onepiece.fandom.com/wiki/Chapter_60",
]
# one_piece_vectorstore.delete_all_documents()

# one_piece_vectorstore.insert_data(one_piece_chapter_links, "url")
# wano_pdf = ["../../Test-Documents/one_piece_kb/wano_guide.pdf"]
# one_piece_vectorstore.insert_data(wano_pdf, "pdf")
# one_piece_vectorstore.insert_data(["https://onepiece.fandom.com/wiki/One_Piece_novel_A"], "url")
# results = one_piece_vectorstore.vector_search("Who is Ace?", top_k=8)
# for result in results:
    # print(result.page_content)
    # print(result.metadata)
    # print("____________________________________________________________________________________________________")