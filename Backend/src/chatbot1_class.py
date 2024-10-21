"""
CHATBOT CLASS, TO MAKE REUSABLE
"""
import sys

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

import uuid

load_dotenv()  # load .env variables


class Chatbot1:
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
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"{systemPrompt} You are capable of answering in " +"{language}",

                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Define a new graph
        self.workflow = StateGraph(state_schema=self.State)
        # Define the (single) node in the graph
        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", self.call_model)

        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)

        self.trimmer = trim_messages(
            max_tokens=500,
            strategy="last",
            token_counter=self.model,
            include_system=True,
            allow_partial=False,
            start_on="human",
        )

        self.config = {"configurable": {"thread_id": self.generate_thread_id}}

        # self.State = self.State()

    # Function that calls the mode
    def call_model(self, state: 'Chatbot1.State'):
        chain = self.prompt | self.model
        trimmed_messages = self.trimmer.invoke(state["messages"])
        response = chain.invoke(
            {"messages": trimmed_messages, "language": state["language"]}
        )
        return {"messages": response}

    def send_message(self, query: str = "Greet me with 'Hi, how can I assist you today?", print: bool = False) -> dict:
        input_messages = [HumanMessage(query)]
        output = self.app.invoke({"messages": input_messages, "language": self.language}, self.config)

        if print:
            output["messages"][-1].pretty_print()

        return output

    def generate_thread_id(self):
        return str(uuid.uuid4())

    class State(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        language: str



" '''''''''''''''''''''''''''''''EXAMPLE OF HOW TO USE THE CLASS''''''''''''''''''''''''''''''' "
chatbot = Chatbot1()
def run_chatbot():
    response = chatbot.send_message(print=False)
    print(f"Chatbot: {response['messages'][-1].content}")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting chatbot...")
            break
        response = chatbot.send_message(user_input, print=False)
        print(f"Chatbot: {response['messages'][-1].content}")

        print("----------------")
        for message in response["messages"]:
            print(message.content)

"''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''"





#nice lil function
def open_new_console():
    """Opens a new console window and runs this script in that window."""
    if sys.platform == "win32":
        # Windows system
        os.system(f'start cmd /k python "{sys.argv[0]}" --run-chatbot')
    elif sys.platform == "linux" or sys.platform == "darwin":
        # Linux or macOS system
        os.system(f'xterm -e python3 "{sys.argv[0]}" --run-chatbot')
    else:
        print("Unsupported operating system for this example.")

if __name__ == "__main__":


    run_chatbot()

""" uncomment to open new console window"""
    # if len(sys.argv) > 1 and sys.argv[1] == '--run-chatbot':
    #     run_chatbot()
    # else:
    #     open_new_console()
