#testing how environment variables work

# from dotenv import load_dotenv
# import os
#
# # Load environment variables from .env file
# load_dotenv()
#
# # Check if the key is being loaded correctly
# api_key = os.getenv('AZURE_OPEN_AI_API_KEY')
# if api_key is None:
#     raise ValueError("AZURE_OPENAI_API_KEY is not set or not found in .env file.")
#
# print(f"Loaded API Key: {api_key}")

from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Print all environment variables to see if the .env was loaded
for key, value in os.environ.items():
    print(f"{key}: {value}")

# Specifically check if AZURE_OPENAI_API_KEY was loaded
print("AZURE_OPENAI_API_KEY:",os.getenv('AZURE_OPEN_AI_API_KEY'))