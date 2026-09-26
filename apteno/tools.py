from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Protocol, TypeVar, cast, runtime_checkable

from apteno.errors import ToolFailure
from apteno.protocols import Tool
from apteno.types import Err, Ok

I = TypeVar("I")
M = TypeVar("M")
O = TypeVar("O")
E = TypeVar("E")
F = TypeVar("F")
Mapped = TypeVar("Mapped")
RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


class ToolRisk(Enum):
    READ_ONLY = "read_only"
    WRITE = "write"
    APPROVAL_REQUIRED = "approval_required"


@runtime_checkable
class ToolSpec(Protocol):
    """SDK-facing schema, codec, and executor for one model-callable tool."""

    name: str
    description: str
    parameters: Mapping[str, object]
    risk: ToolRisk

    def encode_request(self, request: object) -> Mapping[str, object] | None: ...

    def parse_arguments(self, arguments: Mapping[str, object]) -> object: ...

    def execute(self, request: object) -> Ok[object] | Err[ToolFailure]: ...


@dataclass(frozen=True, slots=True)
class ToolDefinition(Generic[RequestT, ResponseT]):

    name: str
    description: str
    parameters: Mapping[str, object]
    request_type: type[RequestT]
    encode: Callable[[RequestT], Mapping[str, object]]
    decode: Callable[[Mapping[str, object]], RequestT]
    handler: Callable[[RequestT], Ok[ResponseT] | Err[ToolFailure]]
    risk: ToolRisk = ToolRisk.APPROVAL_REQUIRED

    def encode_request(self, request: object) -> Mapping[str, object] | None:
        if not isinstance(request, self.request_type):
            return None
        return self.encode(cast(RequestT, request))

    def parse_arguments(self, arguments: Mapping[str, object]) -> RequestT:
        return self.decode(arguments)

    def execute(self, request: object) -> Ok[object] | Err[ToolFailure]:
        if not isinstance(request, self.request_type):
            return Err(ToolFailure(self.name, "Request type does not match tool"))
        result = self.handler(cast(RequestT, request))
        if isinstance(result, Err):
            return result
        return Ok(result.value)


@runtime_checkable
class ToolPlugin(Protocol):
    def create(self, settings: Mapping[str, str]) -> tuple[ToolSpec, ...]: ...


class FunctionalTool(Generic[I, O, E]):
    def __init__(self, function: Callable[[I], Ok[O] | Err[E]]) -> None:
        self._function = function

    def run(self, request: I) -> Ok[O] | Err[E]:
        return self._function(request)


def map_output(
    tool: Tool[I, O, E], function: Callable[[O], Mapped]
) -> FunctionalTool[I, Mapped, E]:
    def run(request: I) -> Ok[Mapped] | Err[E]:
        result = tool.run(request)
        if isinstance(result, Err):
            return result
        return Ok(function(result.value))

    return FunctionalTool(run)


def contramap_input(
    tool: Tool[I, O, E], function: Callable[[Mapped], I]
) -> FunctionalTool[Mapped, O, E]:
    return FunctionalTool(lambda request: tool.run(function(request)))


def compose(
    first: Tool[I, M, E],
    second: Tool[M, O, F],
) -> FunctionalTool[I, O, E | F]:
    def run(request: I) -> Ok[O] | Err[E | F]:
        intermediate = first.run(request)
        if isinstance(intermediate, Err):
            return intermediate
        return second.run(intermediate.value)

    return FunctionalTool(run)
