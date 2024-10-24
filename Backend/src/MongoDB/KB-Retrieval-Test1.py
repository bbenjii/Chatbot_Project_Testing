"""

CODE FOR KNOWLEDGE BASE CREATION AND RETRIEVAL

"""


# pip install -qU langchain langchain-openai langchain-chroma beautifulsoup4
import os

from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import requests
from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
import random


# ____________________AZURE OPENAI API CREDENTIALS___________________________________________________

load_dotenv() #load .env variables

api_endpoint = os.getenv('AZURE_OPENAI_API_KEY')
api_key = os.getenv('AZURE_OPENAI_ENDPOINT')
api_version = os.getenv('OPENAI_API_VERSION')
api_type = os.getenv('OPENAI_API_TYPE')
deployment_model = os.getenv('OPENAI_MODEL')
deployment_name = os.getenv('OPENAI_NAME')


url = "https://www.intact.ca/en/faq"
# url = "https://docs.smith.langchain.com/overview"
url = "https://www.space.com/25126-big-bang-theory.html"
url = "https://naruto.fandom.com/wiki/Naruto_Uzumaki"
url = "https://www.wikihow.com/Grow-a-Beard"


user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6279.207 Safari/537.36 OPR/110.0.4700.152",
    "https://explore.whatismybrowser.com/useragents/parse/809500880-opera-mac-os-x-blink",
    "https://explore.whatismybrowser.com/useragents/parse/809506244-safari-mac-os-x-webkit",
    "https://explore.whatismybrowser.com/useragents/parse/809522130-chrome-mac-os-x-blink",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6279.207 Safari/537.36 OPR/110.0.4700.152"
]

user_agent =  user_agents[random.randint(0,4)]

headers = {
    "User-Agent": user_agent
}

loader = WebBaseLoader(url, header_template=headers)
data = loader.load()
print(len(data))
print(data)

# print(data[0].page_content)
# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
# all_splits = text_splitter.split_documents(data)


# for split in all_splits:
#     split.page_content = (split.page_content.replace("  ","").replace("\n\n",""))

# for split in all_splits:
#     print(split.page_content)
#     print("____________________________")


# vectorstore = Chroma.from_documents(documents=all_splits, embedding=AzureOpenAIEmbeddings())
#
#
# # k is the number of chunks to retrieve
# retriever = vectorstore.as_retriever(k=10)
#
# docs = retriever.invoke("What are the best product to grow a beard faster?")
#
# for doc in docs:
#     print(doc)
#     print("____________________________________")

# print(all_splits)
# for split in all_splits:
#     print(f"Page Content: {split.page_content}")





# file = open("intact_knowledge_base.txt",'a')
#
# for split in all_splits:
#     file.write(split.page_content)
#
#
# # print(soup.get_text())
# file.close()
# print(all_splits)