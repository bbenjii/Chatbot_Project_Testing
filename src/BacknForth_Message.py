"""
SIMPLE LOGIC TO HAVE BACK AND FORTH MESSAGES WITH OPEN AZURE API"""


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

instruction_promp = "You are a helpful assistant that translates English to French. Translate the user sentence."

phrase_to_translate = "I love programming."
messages = [
    (
        "system",
        instruction_promp,
    ),
    ("human", phrase_to_translate),
]

ai_msg = llm.invoke(messages)

print(ai_msg.content)
