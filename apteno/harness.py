from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from apteno.errors import ToolFailure
from apteno.tools import ToolRisk, ToolSpec
from apteno.types import Err, Ok


@runtime_checkable
class ToolAdapters(Protocol):
    @property
    def tools(self) -> tuple[ToolSpec, ...]: ...

    def dispatch(self, request: object) -> Ok[object] | Err[ToolFailure]: ...


@dataclass(frozen=True, slots=True)
class ApprovalRequiredTool:
    """Require permissions before dispatching tool""" # (from repl /tools)

    wrapped: ToolSpec
    risk: ToolRisk = ToolRisk.APPROVAL_REQUIRED

    @property
    def name(self) -> str:
        return self.wrapped.name

    @property
    def description(self) -> str:
        return self.wrapped.description

    @property
    def parameters(self) -> Mapping[str, object]:
        return self.wrapped.parameters

    def encode_request(self, request: object) -> Mapping[str, object] | None:
        return self.wrapped.encode_request(request)

    def parse_arguments(self, arguments: Mapping[str, object]) -> object:
        return self.wrapped.parse_arguments(arguments)

    def execute(self, request: object) -> Ok[object] | Err[ToolFailure]:
        return self.wrapped.execute(request)


class ModularToolAdapters:
    """Registry that composes tool adapters"""

    def __init__(self, *tools: ToolSpec) -> None:
        names = [tool.name for tool in tools]
        duplicates = sorted(name for name in set(names) if names.count(name) > 1)
        if duplicates:
            raise ValueError(f"Duplicate tool definitions: {', '.join(duplicates)}")
        self._tools = tuple(tools)

    @property
    def tools(self) -> tuple[ToolSpec, ...]:
        return self._tools

    def dispatch(self, request: object) -> Ok[object] | Err[ToolFailure]:
        for tool in self._tools:
            if tool.encode_request(request) is not None:
                return tool.execute(request)
        return Err(
            ToolFailure(
                type(request).__name__,
                f"No registered tool accepts {type(request).__name__}",
            )
        )
