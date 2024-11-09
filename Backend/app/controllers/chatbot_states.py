# chatbot_states.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

# Import Chatbot for type checking only, to avoid circular import issues
if TYPE_CHECKING:
    from chatbot_controller import Chatbot


class State(ABC):
    """Base class for all states in the chatbot state machine."""

    def __init__(self, chatbot: "Chatbot", state_name: str):
        self.chatbot = chatbot
        self.state_name = state_name

    @abstractmethod
    def handle(self, query: str):
        """Handle the state's main logic."""
        pass


class IdleState(State):
    """State when chatbot is Idle."""

    def handle(self, query: str):
        print("State: Idle")
        return "user_input"  # Transition to the DecisionState

class UserInputState(State):
    """State for receiving user input."""

    def handle(self, query: str):
        print("State: UserInputState")
        self.chatbot.message_history.append(query)
        return "decision"  # Transition to the DecisionState


class DecisionState(State):
    """State to decide if a vector search is needed."""


    def handle(self, query: str):
        print("State: DecisionState")
        if self.chatbot.is_search_tool_required(query):
            return "vector_search"  # Transition to VectorSearchState
        return "response"  # Transition to ResponseState


class VectorSearchState(State):
    """State to perform vector search and fetch context."""

    def handle(self, query: str):
        print("State: VectorSearchState")
        context = self.chatbot.retrieve_context(query)
        self.chatbot.context = context  # Store context for use in response
        return "response"  # Transition to ResponseState


class ResponseState(State):
    """State to generate the chatbot's response."""

    def handle(self, query: str):
        print("State: ResponseState")
        messages = self.chatbot.construct_messages(self.chatbot.message_history, self.chatbot.context)
        response = self.chatbot.model.invoke(messages)
        self.chatbot.message_history.append(response.content)
        return "idle"

class StateMachine:
    def __init__(self, chatbot: "Chatbot"):
        self.chatbot = chatbot
        self.states = {
            "idle": IdleState(self.chatbot, "idle"),
            "user_input": UserInputState(self.chatbot, "user_input"),
            "decision": DecisionState(self.chatbot, "decision"),
            "vector_search": VectorSearchState(self.chatbot, "vector_search"),
            "response": ResponseState(self.chatbot, "response")
        }
        self.current_state = self.states["idle"]

    def run(self, query: str):
        """Execute the current state and transition to the next state."""

        next_state_name = self.current_state.handle(query)
        self.current_state = self.states.get(next_state_name)

        while self.current_state.state_name != "idle":
            next_state_name = self.current_state.handle(query)
            self.current_state = self.states.get(next_state_name)
            # return self.current_state