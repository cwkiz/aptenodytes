from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

@dataclass(frozen=True, slots=True)
class ToolFailure:
    name: str
    message: str


@dataclass(frozen=True, slots=True)
class AgentFailure:
    message: str


@dataclass(frozen=True, slots=True)
class UndeclaredTool:
    name: str


@dataclass(frozen=True, slots=True)
class InvalidToolCall:
    message: str


@dataclass(frozen=True, slots=True)
class MaxToolRounds:
    limit: int


AgentError: TypeAlias = AgentFailure | UndeclaredTool | InvalidToolCall | MaxToolRounds
