# app/core/chatbot_states.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging
from enum import Enum

from app.core.exceptions import AppException
from app.services.vector_service import VectorService
from app.models.chatbot import ChatbotMessage


# logging.basicConfig(
#     level=logging.INFO,
# )

logger = logging.getLogger(__name__)


class StateType(Enum):
    IDLE = "idle"
    USER_INPUT = "user_input"
    TOOL_SELECTION = "tool_selection"
    VECTOR_SEARCH = "vector_search"
    FUNCTION_CALL = "function_call"
    RESPONSE = "response"
    ERROR = "error"


class ChatbotContext:
    """Context object to maintain chatbot state and data."""

    def __init__(self,
                 user_id: str,
                 thread_id: str,
                 message_history: List[Dict[str, Any]]):
        self.user_id = user_id
        self.thread_id = thread_id
        self.message_history = message_history
        self.current_message: Optional[str] = None
        self.current_context: Optional[str] = None
        self.tool_results: Dict[str, Any] = {}
        self.response: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        self.start_time = datetime.now(timezone.utc)
        self.error: Optional[Exception] = None


class State(ABC):
    """Abstract base class for all chatbot states."""

    def __init__(self, name: StateType, services: Dict[str, Any]):
        self.name = name
        self.services = services
        self.logger = logging.getLogger(f"ChatbotState.{name.value}")

    @abstractmethod
    async def handle(self, context: ChatbotContext) -> StateType:
        """Handle the current state and return next state."""
        pass

    async def log_transition(self, context: ChatbotContext, next_state: StateType):
        """Log state transition with context details."""
        duration = (datetime.now(timezone.utc) - context.start_time).total_seconds()
        self.logger.info(
            f"State transition: {self.name.value} -> {next_state.value} "
            f"(Duration: {duration:.2f}s, Thread: {context.thread_id})"
        )


class IdleState(State):
    """Initial state of the chatbot system."""

    def __init__(self, services: Dict[str, Any]):
        super().__init__(StateType.IDLE, services)

    async def handle(self, context: ChatbotContext) -> StateType:
        try:
            if not context.current_message:
                raise AppException("No message provided")

            # Reset context for new interaction
            context.tool_results = {}
            context.current_context = None
            context.response = None
            context.metadata = {}

            await self.log_transition(context, StateType.USER_INPUT)
            return StateType.USER_INPUT

        except Exception as e:
            context.error = e
            return StateType.ERROR


class UserInputState(State):
    """Process and validate user input."""

    def __init__(self, services: Dict[str, Any]):
        super().__init__(StateType.USER_INPUT, services)

    async def handle(self, context: ChatbotContext) -> StateType:
        try:
            # Save the message to history
            await self.services['message_model'].create_message(
                thread_id=context.thread_id,
                user_id=context.user_id,
                role="human",
                content=context.current_message,
                metadata={"timestamp": datetime.now(timezone.utc).isoformat()}
            )

            await self.log_transition(context, StateType.TOOL_SELECTION)
            return StateType.TOOL_SELECTION

        except Exception as e:
            context.error = e
            return StateType.ERROR


class ToolSelectionState(State):
    """Determine which tools to use for the response."""

    def __init__(self, services: Dict[str, Any]):
        super().__init__(StateType.TOOL_SELECTION, services)

    async def handle(self, context: ChatbotContext) -> StateType:
        try:
            # Tool selection prompt
            tool_selection_messages = [{
                "role": "system",
                "content": """Analyze the user query and determine which tools are needed.
                Available tools:
                - vector_search: Search for relevant information in the knowledge base

                Respond with a JSON array of required tools, or empty array if no tools needed."""
            }, {
                "role": "user",
                "content": context.current_message
            }]

            # Get tool selection decision
            response = await self.services['model'].ainvoke(tool_selection_messages)
            tools_needed = self._parse_tool_response(response.content)

            # Store tools in context
            context.metadata['selected_tools'] = tools_needed

            # Determine next state based on tools
            if 'vector_search' in tools_needed:
                await self.log_transition(context, StateType.VECTOR_SEARCH)
                return StateType.VECTOR_SEARCH

            await self.log_transition(context, StateType.RESPONSE)
            return StateType.RESPONSE

        except Exception as e:
            context.error = e
            return StateType.ERROR

    def _parse_tool_response(self, response: str) -> List[str]:
        """Parse the tool selection response."""
        try:
            import json
            tools = json.loads(response)
            return [tool.strip() for tool in tools if isinstance(tool, str)]
        except:
            return []


class VectorSearchState(State):
    """Perform vector search for relevant context."""

    def __init__(self, services: Dict[str, Any]):
        super().__init__(StateType.VECTOR_SEARCH, services)
        self.vector_service = services['vector_service']

    async def handle(self, context: ChatbotContext) -> StateType:
        try:
            # Perform vector search
            results = await self.vector_service.search_similar(
                user_id=context.user_id,
                query=context.current_message,
                limit=3
            )

            # Store results in context
            context.tool_results['vector_search'] = results
            context.current_context = self._format_context(results)

            await self.log_transition(context, StateType.RESPONSE)
            return StateType.RESPONSE

        except Exception as e:
            context.error = e
            return StateType.ERROR

    def _format_context(self, results: List[Dict[str, Any]]) -> str:
        """Format vector search results as context."""
        if not results:
            return ""

        context = "Relevant information:\n\n"
        for idx, result in enumerate(results, 1):
            context += f"{idx}. {result['text_content']}\n\n"
        return context


class ResponseState(State):
    """Generate final response using available context and tool results."""

    def __init__(self, services: Dict[str, Any]):
        super().__init__(StateType.RESPONSE, services)

    async def handle(self, context: ChatbotContext) -> StateType:
        try:
            # Construct messages with context
            messages = self._construct_messages(context)

            # Generate response
            response = await self.services['model'].ainvoke(messages)
            context.response = response.content

            # Save chatbot message
            await self.services['message_model'].create_message(
                thread_id=context.thread_id,
                user_id=context.user_id,
                role="assistant",
                content=response.content,
                metadata={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tools_used": context.metadata.get('selected_tools', []),
                    "context_used": bool(context.current_context),
                    "tool_results": context.tool_results
                }
            )

            await self.log_transition(context, StateType.IDLE)
            return StateType.IDLE

        except Exception as e:
            context.error = e
            return StateType.ERROR

    def _construct_messages(self, context: ChatbotContext) -> List[Dict[str, str]]:
        """Construct messages for the model."""
        system_content = self._get_system_prompt(context)

        messages = [{
            "role": "system",
            "content": system_content
        }]

        # Add message history
        messages.extend(context.message_history[-5:])  # Last 5 messages

        # Add current message
        messages.append({
            "role": "user",
            "content": context.current_message
        })

        return messages

    def _get_system_prompt(self, context: ChatbotContext) -> str:
        """Get system prompt with context."""
        prompt = (
            "You are a helpful virtual chatbot. "
            "Format your responses in Markdown for better readability. "
            "Be concise yet informative, and use bullet points when appropriate. "
            "Make key terms and phrases bold using **asterisks**."
        )

        if context.current_context:
            prompt += f"\n\nUse this context for your response:\n{context.current_context}"

        return prompt


class ErrorState(State):
    """Handle error conditions."""

    def __init__(self, services: Dict[str, Any]):
        super().__init__(StateType.ERROR, services)

    async def handle(self, context: ChatbotContext) -> StateType:
        try:
            error_message = str(context.error) if context.error else "Unknown error"
            self.logger.error(f"Error in state machine: {error_message}")

            # Save error message
            await self.services['message_model'].create_message(
                thread_id=context.thread_id,
                user_id=context.user_id,
                role="system",
                content="I encountered an error processing your request. Please try again.",
                metadata={
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": error_message,
                    "state": context.metadata.get('current_state', 'unknown')
                }
            )

            await self.log_transition(context, StateType.IDLE)
            return StateType.IDLE

        except Exception as e:
            self.logger.error(f"Error handling error state: {e}")
            return StateType.IDLE


class ChatbotStateMachine:
    """Manages state transitions for the chatbot system."""

    def __init__(self, services: Dict[str, Any]):
        self.services = services
        self.states = {
            StateType.IDLE: IdleState(services),
            StateType.USER_INPUT: UserInputState(services),
            StateType.TOOL_SELECTION: ToolSelectionState(services),
            StateType.VECTOR_SEARCH: VectorSearchState(services),
            StateType.RESPONSE: ResponseState(services),
            StateType.ERROR: ErrorState(services)
        }
        self.current_state = StateType.IDLE
        self.logger = logging.getLogger("ChatbotStateMachine")

    async def process_message(
            self,
            user_id: str,
            thread_id: str,
            message: str,
            message_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a message through the state machine."""
        context = ChatbotContext(user_id, thread_id, message_history)
        context.current_message = message

        try:
            while True:
                state_handler = self.states[self.current_state]
                context.metadata['current_state'] = self.current_state.value

                self.current_state = await state_handler.handle(context)

                if self.current_state == StateType.IDLE:
                    break

            return {
                "response": context.response,
                "metadata": context.metadata,
                "tool_results": context.tool_results
            }

        except Exception as e:
            self.logger.error(f"Unhandled error in state machine: {e}")
            raise AppException("Failed to process message")