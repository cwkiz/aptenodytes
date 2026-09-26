from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

_FOCUS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("imports", re.compile(r"^\s*import\s+([\w.]+)", re.MULTILINE)),
    ("namespaces", re.compile(r"^\s*namespace\s+([\w'.]+)", re.MULTILINE)),
    ("declarations", re.compile(r"^\s*(?:theorem|lemma|example|def)\s+([\w'.]+)", re.MULTILINE)),
    ("signatures", re.compile(r"^\s*(?:theorem|lemma|example|def)\s+.+", re.MULTILINE)),
    ("holes", re.compile(r"\b(?:sorry|admit)\b")),
    ("tactics", re.compile(r"\b(?:intro|exact|apply|simp|rw|rfl|induction|omega|aesop|constructor)\b")),
    ("structures", re.compile(r"^\s*(?:class|structure|inductive)\s+([\w'.]+)", re.MULTILINE)),
    ("universes", re.compile(r"^\s*universe\s+(.+)", re.MULTILINE)),
)

_MAX_SOURCE_CHARS = 24_000
_MAX_ITEMS_PER_SIGNAL = 12
_MAX_SIGNAL_CHARS = 1_200
_MAX_TARGETS = 8
_MAX_CONTEXT_CHARS = 6_000


@dataclass(frozen=True, slots=True)
class LeanFocus:
    imports: tuple[str, ...]
    namespaces: tuple[str, ...]
    declarations: tuple[str, ...]
    signatures: tuple[str, ...]
    tactics: tuple[str, ...]
    has_holes: bool
    structures: tuple[str, ...]
    universes: tuple[str, ...]

    def as_prompt(self) -> str:
        fields = (
            ("imports", self.imports),
            ("namespaces", self.namespaces),
            ("declarations", self.declarations),
            ("signatures", self.signatures),
            ("tactics", self.tactics),
            ("structures", self.structures),
            ("universes", self.universes),
        )
        lines = [
            f"{label}: {', '.join(values)}"
            for label, values in fields
            if values
        ]
        if self.has_holes:
            lines.append("unfinished proof markers: present")
        return "\n".join(lines) if lines else "no declars recognized"


def analyze_lean_source(source: str) -> LeanFocus:
    source = source[:_MAX_SOURCE_CHARS]
    matches = {
        name: tuple(
            value[:_MAX_SIGNAL_CHARS]
            for value in pattern.findall(source)[:_MAX_ITEMS_PER_SIGNAL]
        )
        for name, pattern in _FOCUS_PATTERNS
    }
    return LeanFocus(
        imports=tuple(dict.fromkeys(matches["imports"])),
        namespaces=tuple(dict.fromkeys(matches["namespaces"])),
        declarations=tuple(dict.fromkeys(matches["declarations"])),
        signatures=tuple(dict.fromkeys(matches["signatures"])),
        tactics=tuple(dict.fromkeys(matches["tactics"])),
        has_holes=bool(matches["holes"]),
        structures=tuple(dict.fromkeys(matches["structures"])),
        universes=tuple(dict.fromkeys(matches["universes"])),
    )


def analyze_target_sources(
    sources: Mapping[str, str],
    *,
    max_files: int = _MAX_TARGETS,
    max_chars: int = _MAX_CONTEXT_CHARS,
) -> str:
    if max_files < 1 or max_chars < 1:
        raise ValueError("focus limits must be positive")
    if len(sources) > min(max_files, _MAX_TARGETS):
        raise ValueError(f"heuristics helper accepts at most {_MAX_TARGETS} target files!")
    sections: list[str] = []
    remaining = min(max_chars, _MAX_CONTEXT_CHARS)
    for path, source in sources.items():
        summary = analyze_lean_source(source).as_prompt()
        section = f"{path}\n{summary}"
        if len(section) > remaining:
            marker = "\n[LeanFocus summary truncated]"
            section = (
                section[: remaining - len(marker)] + marker
                if remaining > len(marker)
                else marker[:remaining]
            )
        sections.append(section)
        remaining -= len(section)
        if remaining <= 0:
            break
    if not sections:
        return "no target Lean files were analyzed"
    return "\n\n".join(sections)
