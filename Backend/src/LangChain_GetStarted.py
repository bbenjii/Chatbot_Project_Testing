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
#
# load_dotenv() #load .env variables
#
#
# # already done in the .env file
# # os.environ["AZURE_OPENAI_API_KEY"] = api_key
# # os.environ["AZURE_OPENAI_ENDPOINT"] = api_endpoint
#
# print(os.environ["AZURE_OPENAI_API_KEY"])
# llm = AzureChatOpenAI(
#     azure_deployment = os.getenv('OPENAI_NAME'),  # or your deployment
#     api_version = os.getenv('OPENAI_API_VERSION'),  # or your api version
#     temperature = 0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
#     model = os.getenv('OPENAI_MODEL')
# )
#
# # __________________________ MESSAGE HANDLING________________________________________________
#
# instruction_promp = "You are a helpful assistant that translates English to French. Translate the user sentence."
#
# phrase_to_translate = "I love programming."
# messages = [
#     (
#         "system",
#         instruction_promp,
#     ),
#     ("human", phrase_to_translate),
# ]
#
# ai_msg = llm.invoke(messages)
#
# print(ai_msg.content)
