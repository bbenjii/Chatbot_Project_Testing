"""
CHATBOT Controller, TO MAKE REUSABLE
"""

"""_____________________________IMPORTS_________________________________________"""
# must install: pip install langchain-openai
#              pip install -U langchain-openai
import os
import uuid
from typing import Sequence, List

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_openai import AzureChatOpenAI
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from .chatbot_states import StateMachine  # Import the StateMachine class
from .vector_store_controller import vectorStore_controller

# from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, trim_messages

load_dotenv()  # load .env variables


def HumanMessage(message: str):
    return ("human", message)


def SystemMessage(message: str):
    return ("system", message)


def AIMessage(message: str):
    return ("ai", message)


class Chatbot:
    def __init__(self, systemPrompt="You are a helpful assistant.", language="all languages"):
        self.model = AzureChatOpenAI(
            azure_deployment=os.getenv('OPENAI_NAME'),  # or your deployment
            api_version=os.getenv('OPENAI_API_VERSION'),  # or your api version
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            model=os.getenv('OPENAI_MODEL')
        )

        # Initialize State Machine
        self.state_machine = StateMachine(self)

        self.language = language
        self.systemPrompt = systemPrompt
        self.message_history = []
        self.context = ""
        self.thread_id = self.generate_thread_id()

        # self.vector_name = "One-Piece-KB_2"
        self.vector_name = "QC_Life_Docs"
        self.vectorStore = vectorStore_controller(collection_name=self.vector_name)

        self.SearchTool = self.VectorSearchTool(self.vectorStore)

    def is_search_tool_required(self, query):
        system_message = (
            "You are a tool selector for a chatbot answering questions about QC Life. "
            "Determine if the user's message needs context retrieval. Reply with 'yes' or 'no' only."
        )

        prompt = [SystemMessage(system_message), HumanMessage(query)]
        response = self.model.invoke(prompt)
        return response.content.strip().lower() == "yes"

    def retrieve_context(self, query):
        retrieved_data = self.vectorStore.vector_search(query, top_k=4)
        context = ""
        context = "\n".join(f"- {doc.page_content}" for doc in retrieved_data)
        return context

    def construct_messages(self, messages: List[BaseMessage], context: str = "") -> str:
        # Build the system message with  context
        system_message = (
            f"{self.systemPrompt} You are capable of answering in {self.language}. "
            f"Use the following context if procided:\n\nContext{context}\n\n"
            # f"If the context does not contain the answer, say that you don't know. Format your answer in an informative, Markdown-friendly manner. "
            # f"Start with a brief introduction, provide the main information in a structured format (use bullet points if necessary), "
            # f"and end with a polite question, asking if further assistance is needed. "
            # f"Keep your answers as concise as possible unless more details are requested. The fewer lines the better"
            # f"Use Markdown formatting to make key terms and phrases bold (e.g., **important**), but avoid including extraneous characters. "
            # f"Your response will be rendered as HTML.\n\n"
        )

        if context != "":
            # Conversation history
            prompt = [SystemMessage(system_message)] + messages
        else:
            prompt = [SystemMessage(self.systemPrompt)] + messages

        return prompt

    def send_message(self, query: str):
        """Starts the state machine for processing a user query."""
        self.context = ""
        self.state_machine.run(query)

        # Prepare the output
        output = {
            "message_history": self.message_history,
            "ai_message": self.message_history[-1]
        }

        return output


    def generate_thread_id(self):
        return str(uuid.uuid4())

    class State(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        language: str

    class VectorSearchTool:
        def __init__(self, database):
            self.name = "Vector_Search_Tool"
            self.description = "This tool performs a vector search on a user query"
            self.database = database

        def run(self, query: str = ""):
            if query == "":
                return ""

            retrieved_data = self.database.vector_search(query, top_k=4)
            context = ""
            for doc in retrieved_data:
                context += f"\n- Source: {str(doc.metadata)} \n- Content: {str(doc.page_content)} \n"

            return context


# " '''''''''''''''''''''''''''''''EXAMPLE OF HOW TO USE THE CLASS''''''''''''''''''''''''''''''' "
# Example of how to use the class
def run_chatbot():
    chatbot = Chatbot()
    print("Chatbot is ready to chat. Type 'exit' or 'quit' to end the conversation.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting chatbot...")
            break
        response = chatbot.send_message(user_input)

        print(response)

# if __name__ == "__main__":
#
#
#     run_chatbot()
#
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
