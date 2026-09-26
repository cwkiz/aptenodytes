from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from apteno.types import Err, Ok

I_contra = TypeVar("I_contra", contravariant=True)
O_co = TypeVar("O_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)


@runtime_checkable
class Tool(Protocol[I_contra, O_co, E_co]):
    """a composable boundary"""

    def run(self, request: I_contra) -> Ok[O_co] | Err[E_co]: ...
