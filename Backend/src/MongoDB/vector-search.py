import os
from dotenv import load_dotenv

# LangChain imports
from langchain_openai import AzureOpenAIEmbeddings
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()  # Load environment variables

# Initialize MongoDB client
MONGODB_ATLAS_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_ATLAS_URI, server_api=ServerApi('1'))
db = client["Chatbot-Test"]
collection = db["QC_Life_Docs"]

# Setup for MongoDB Atlas Vector Store
embeddings_model = AzureOpenAIEmbeddings(azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"))
vector_store = MongoDBAtlasVectorSearch(
    collection=collection,
    embedding=embeddings_model,
    index_name="vector_query_index",  # Your vector search index in MongoDB Atlas
    relevance_score_fn="cosine"  # Specify the similarity function (cosine in this case)
)


# Perform vector search
def vector_search(query, top_k=3):
    # Generate embedding for the query using the same embedding model
    query_embedding = embeddings_model.embed_documents([query])[0]

    # Perform similarity search in MongoDB Atlas vector store
    results = vector_store.similarity_search(query, k=top_k)

    # Print the results
    for result in results:
        print(result)
        # print(f"Document: {result.metadata['title']}")
        print(f"Chunk: {result.page_content}")
        # print(f"Metadata: {result.metadata}")
        print("------\n")


# Example usage: search for a specific term
query = "Whats QC Life"
vector_search(query, top_k=3)
