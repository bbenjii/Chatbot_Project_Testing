"""
CHATBOT Controller, TO MAKE REUSABLE
"""
import sys

"""_____________________________IMPORTS_________________________________________"""
# must install: pip install langchain-openai
#              pip install -U langchain-openai
import os
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from .vector_store_controller import vectorStore_controller


from typing import Sequence, List

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

# from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, trim_messages

import uuid

load_dotenv()  # load .env variables

def HumanMessage(message : str):
    return ("human", message)

def SystemMessage(message : str):
    return ("system", message)

def AIMessage(message : str):
    return ("ai", message)

class Chatbot:
    def __init__(self, systemPrompt = "You are a helpful assistant.", language = "all languages"):
        self.model = AzureChatOpenAI(
            azure_deployment=os.getenv('OPENAI_NAME'),  # or your deployment
            api_version=os.getenv('OPENAI_API_VERSION'),  # or your api version
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            model=os.getenv('OPENAI_MODEL')
        )
        self.language = language

        self.systemPrompt = systemPrompt

        self.messageHistory = []
        self.thread_id = self.generate_thread_id()

        # self.vector_name = "One-Piece-KB_2"
        self.vector_name = "QC_Life_Docs"

        self.vectorStore = vectorStore_controller(collection_name= self.vector_name)

    def retrieve_context(self, query):
        retrieved_data = self.vectorStore.vector_search(query, top_k=4)
        context =""
        for doc in retrieved_data:
            context += f"\n- Source: {str(doc.metadata)} \n- Content: {str(doc.page_content)} \n"

        return context


    def send_message(self, query: str, print_output: bool = False):
        # Append the user's message to the conversation history
        self.messageHistory.append(HumanMessage(query))

        # Context is empty for now; to be implemented later
        context = self.retrieve_context(query)

        # Construct the messages for the model
        messages = self.construct_messages(self.messageHistory, context)

        # Invoke the model with the messages
        response = self.model.invoke(messages)

        # Append the AI's response to the conversation history
        ai_message = AIMessage(response.content)
        self.messageHistory.append(ai_message)

        # Prepare the output
        output = {
            "message_history": self.messageHistory,
            "ai_message": response.content
        }
        if print_output:
            print(ai_message)

        return output



    def construct_messages(self, messages: List[BaseMessage], context: str = "") -> str:
        # Build the system message with  context
        system_message = (f"{self.systemPrompt} You are capable of answering in {self.language}. "
 f"Use the following context to answer the question:\n\n{context} "
 f"If the context does not contain the answer, say that you don't know. Format your answer in an informative, Markdown-friendly manner. "
 f"Start with a brief introduction, provide the main information in a structured format (use bullet points if necessary), "
 f"and end with a polite question, asking if further assistance is needed. "
 f"Use Markdown formatting to make key terms and phrases bold (e.g., **important**), but avoid including extraneous characters. "
 f"Your response will be rendered as HTML.\n\n")

        #Conversation history
        combined_messages = [SystemMessage(system_message)] + messages

        # prompt = f"{system_message}\n\n{conversation_history}\n{context}"
        return combined_messages

    def generate_thread_id(self):
        return str(uuid.uuid4())

    class State(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        language: str
#
#
#
# " '''''''''''''''''''''''''''''''EXAMPLE OF HOW TO USE THE CLASS''''''''''''''''''''''''''''''' "
# Example of how to use the class
# def run_chatbot():
#     chatbot = Chatbot()
#     print("Chatbot is ready to chat. Type 'exit' or 'quit' to end the conversation.")
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() in ['exit', 'quit']:
#             print("Exiting chatbot...")
#             break
#         response = chatbot.send_message(user_input)
#
#         print(response)

#
#
# "''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''"
#
#
#
#
#
# #nice lil function
# def open_new_console():
#     """Opens a new console window and runs this script in that window."""
#     if sys.platform == "win32":
#         # Windows system
#         os.system(f'start cmd /k python "{sys.argv[0]}" --run-chatbot')
#     elif sys.platform == "linux" or sys.platform == "darwin":
#         # Linux or macOS system
#         os.system(f'xterm -e python3 "{sys.argv[0]}" --run-chatbot')
#     else:
#         print("Unsupported operating system for this example.")
#
# if __name__ == "__main__":
#
#
#     run_chatbot()
#
# """ uncomment to open new console window"""
#     # if len(sys.argv) > 1 and sys.argv[1] == '--run-chatbot':
#     #     run_chatbot()
#     # else:
#     #     open_new_console()
