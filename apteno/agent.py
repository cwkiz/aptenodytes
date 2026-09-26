from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from apteno.errors import (
    AgentError,
    AgentFailure,
    InvalidToolCall,
    MaxToolRounds,
    ToolFailure,
    UndeclaredTool,
)
from apteno.tools import (
    ToolAdapters,
    ToolSpec,
)
from apteno.types import Err, Ok


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class ToolCall:
    id: str
    request: object


@dataclass(frozen=True, slots=True)
class Message:
    role: Role
    content: str
    tool_name: str | None = None
    tool_call_id: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    tool_response: object | None = None
    tool_error: ToolFailure | None = None


@dataclass(frozen=True, slots=True)
class Completion:
    content: str
    tool_calls: tuple[ToolCall, ...] = ()


@dataclass(frozen=True, slots=True)
class AgentRequest:
    messages: tuple[Message, ...]
    tools: tuple[ToolSpec, ...]


@dataclass(frozen=True, slots=True)
class Turn:
    messages: tuple[Message, ...]
    answer: str


class AgentClient(Protocol):
    def complete(self, request: AgentRequest) -> Ok[Completion] | Err[AgentFailure]:
        ...


class Agent(Protocol):
    def turn(self, messages: tuple[Message, ...], user_content: str) -> Ok[Turn] | Err[AgentError]:
        ...


class AgentSession:
    def __init__(
        self,
        backend: AgentClient,
        tools: ToolAdapters,
        max_tool_rounds: int = 8,
    ) -> None:
        if max_tool_rounds < 0:
            raise ValueError("max_tool_rounds must not be negative")
        self.backend = backend
        self.tools = tools
        self.max_tool_rounds = max_tool_rounds

    def turn(
        self, messages: tuple[Message, ...], user_content: str
    ) -> Ok[Turn] | Err[AgentError]:
        history = messages + (Message(Role.USER, user_content),)
        rounds = 0
        while True:
            completion_result = self.backend.complete(
                AgentRequest(history, self.tools.tools)
            )
            if isinstance(completion_result, Err):
                return Err(completion_result.error)
            completion = completion_result.value
            history += (
                Message(
                    Role.ASSISTANT,
                    completion.content,
                    tool_calls=completion.tool_calls,
                ),
            )
            if not completion.tool_calls:
                return Ok(Turn(history, completion.content))
            if rounds >= self.max_tool_rounds:
                return Err(MaxToolRounds(self.max_tool_rounds))
            for call in completion.tool_calls:
                if not call.id.strip():
                    return Err(InvalidToolCall("tool call id must not be empty"))
                matching = next(
                    (
                        tool
                        for tool in self.tools.tools
                        if tool.encode_request(call.request) is not None
                    ),
                    None,
                )
                if matching is None:
                    return Err(UndeclaredTool(type(call.request).__name__))
                name = matching.name
                result = self.tools.dispatch(call.request)
                if isinstance(result, Ok):
                    history += (
                        Message(
                            Role.TOOL,
                            str(result.value),
                            tool_name=name,
                            tool_call_id=call.id,
                            tool_response=result.value,
                        ),
                    )
                else:
                    history += (
                        Message(
                            Role.TOOL,
                            f"{result.error.name}: {result.error.message}",
                            tool_name=name,
                            tool_call_id=call.id,
                            tool_error=result.error,
                        ),
                    )
            rounds += 1


def format_agent_error(error: AgentError) -> str:
    if isinstance(error, AgentFailure):
        return f"Agent backend error: {error.message}"
    if isinstance(error, UndeclaredTool):
        return f"Agent requested undeclared capability: {error.name}"
    if isinstance(error, InvalidToolCall):
        return f"Invalid agent tool call: {error.message}"
    if isinstance(error, MaxToolRounds):
        return f"Agent exceeded the tool round limit ({error.limit})"
    raise TypeError(f"Unknown agent error: {error!r}")
