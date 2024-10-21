"""
LANGCHAIN AZURECHATOPENAI GETSTARTED CODE
source: https://python.langchain.com/v0.2/docs/integrations/chat/azure_chat_openai/
        https://python.langchain.com/v0.2/api_reference/openai/chat_models/langchain_openai.chat_models.azure.AzureChatOpenAI.html

SIMPLE CODE, THAT SHOWS HOW TO USE LANGCHAIN TO CONNECT TO AZURE OPEN AI API AND TRANSLATE A PHRASE TO FRENCH
"""


"""_____________________________IMPORTS_________________________________________"""
# must install: pip install langchain-openai
#              pip install -U langchain-openai
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

""" ____________________ SETUP ___________________________________________________"""

load_dotenv() #load .env variables

api_endpoint = os.getenv('AZURE_OPENAI_API_KEY')
api_key = os.getenv('AZURE_OPENAI_ENDPOINT')
api_version = os.getenv('OPENAI_API_VERSION')
api_type = os.getenv('OPENAI_API_TYPE')
deployment_model = os.getenv('OPENAI_MODEL')
deployment_name = os.getenv('OPENAI_NAME')


# already done in the .env file
# os.environ["AZURE_OPENAI_API_KEY"] = api_key
# os.environ["AZURE_OPENAI_ENDPOINT"] = api_endpoint


llm = AzureChatOpenAI(
    azure_deployment=deployment_name,  # or your deployment
    api_version=api_version,  # or your api version
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    model=deployment_model
)

# __________________________ MESSAGE HANDLING________________________________________________

messages = [
    ("system", "You are an AI assistant that helps people find information.")
]

print("Chatbot: Hello, ask me anything! In French or English!")
while True:
    question = input("\nYou: ")
    messages.append(("human", question))
    response = llm.invoke(messages).content
    print("\nChatbot:", response)
    messages.append(("system", response))