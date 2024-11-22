"""
LANGCHAIN BUILD A CHATBOT TUTORIAL

source: https://python.langchain.com/v0.2/docs/tutorials/chatbot/

CODE THAT SHOWS HOW TO BUILD A CHATBOT WITH LANGCHAIN FRAMEWORKS, WITH COMMON USEFUL FEATURES

FEATURES: CHAT MEMORY/HISTORY, PROMPTS, TRIMMING MESSAGES, GRAPH
"""
from langchain_core.messages import HumanMessage

"""_____________________________IMPORTS_________________________________________"""
# must install: pip install langchain-openai
#              pip install -U langchain-openai
import os
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from typing import Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, trim_messages

""" ____________________ SETUP ___________________________________________________"""

load_dotenv() #load .env variables

model = AzureChatOpenAI(
    azure_deployment = os.getenv('OPENAI_NAME'),  # or your deployment
    api_version = os.getenv('OPENAI_API_VERSION'),  # or your api version
    temperature = 0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    model = os.getenv('OPENAI_MODEL')
)

# __________________________ MESSAGE HANDLING________________________________________________

messages = [
    ("system", "You are an AI assistant that helps people find information.")
]

print("Chatbot: Hello, ask me anything! In French or English!")
while True:
    question = input("\nYou: ")
    messages.append(("human", question))
    response = model.invoke(messages).content
    print("\nChatbot:", response)
    messages.append(("system", response))

# __________________________ MESSAGE PERSISTENCE ________________________________________________

#
# class State(TypedDict):
#     messages: Annotated[Sequence[BaseMessage], add_messages]
#     language: str
#
# # Define a new graph
#
#
#
# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             "You are a helpful assistant. Answer all questions to the best of your ability in {language}.",
#         ),
#         MessagesPlaceholder(variable_name="messages"),
#     ]
# )
# workflow = StateGraph(state_schema = State)
#
# trimmer = trim_messages(
#     max_tokens=65,
#     strategy="last",
#     token_counter=model,
#     include_system=True,
#     allow_partial=False,
#     start_on="human",
# )
#
# # Function that calls the mode
# def call_model(state: State):
#     chain = prompt | model
#     trimmed_messages = trimmer.invoke(state["messages"])
#     response = chain.invoke(
#         {"messages": trimmed_messages, "language": state["language"]}
#     )
#     return {"messages": response}
#
# # Define the (single) node in the graph
# workflow.add_edge(START, "model")
# workflow.add_node("model", call_model)
#
# memory = MemorySaver()
# app_old = workflow.compile(checkpointer=memory)
#
# config = {"configurable": {"thread_id": "abc123"}}
# query = "Hi, I'm Ben"
# language = "French"
#
#
#
# input_messages = [HumanMessage(query)]
# output = app_old.invoke({"messages": input_messages, "language": language}, config)
# output["messages"][-1].pretty_print()
#
# messages = [
#     SystemMessage(content="you're a good assistant"),
#     HumanMessage(content="hi! I'm bob"),
#     AIMessage(content="hi!"),
#     HumanMessage(content="I like vanilla ice cream"),
#     AIMessage(content="nice"),
#     HumanMessage(content="whats 2 + 2"),
#     AIMessage(content="4"),
#     HumanMessage(content="thanks"),
#     AIMessage(content="no problem!"),
#     HumanMessage(content="having fun?"),
#     AIMessage(content="yes!"),
# ]
# # output = app_old.invoke({"messages": messages}, config)
#
#
# config2 = {"configurable": {"thread_id": "abc123"}} #id reffering to an existing conversation
# input_messages = [HumanMessage("what's my name?")]
# output = app_old.invoke({"messages": input_messages}, config2)
# output["messages"][-1].pretty_print()
#
#
#
