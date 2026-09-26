from __future__ import annotations

from apteno.errors import ToolFailure
from apteno.tools import ToolAdapters, ToolSpec
from apteno.types import Err, Ok


class ModularToolAdapters:
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
