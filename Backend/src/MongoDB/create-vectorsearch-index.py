from pymongo import MongoClient
import os
from dotenv import load_dotenv
from pymongo.operations import SearchIndexModel

# Load environment variables
load_dotenv()

# Replace with your MongoDB Atlas connection string
MONGODB_ATLAS_URI = os.getenv("MONGODB_URI")

# Define the database and collection
DATABASE_NAME = "Chatbot-Test"  # Your database name
COLLECTION_NAME = "QC_Life_Docs"  # Your collection name
INDEX_NAME = "vector_query_index"  # The name of your index

# Initialize MongoDB client
client = MongoClient(MONGODB_ATLAS_URI)

# Connect to the specific database and collection
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

def create_vector_search_index():
    try:
        # Define the vector search index
        index = {
            "name": INDEX_NAME,  # The index name
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "numDimensions": 1536,  # Adjust this to match the dimensionality of your embeddings (e.g., OpenAI embeddings have 1536 dimensions)
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
        result = collection.create_search_index(model=search_index_model)

        print(f"Index created: {result}")

    except Exception as e:
        print(f"Error creating index: {e}")
    finally:
        # Close the MongoDB connection
        client.close()

# Run the function to create the vector search index
create_vector_search_index()
