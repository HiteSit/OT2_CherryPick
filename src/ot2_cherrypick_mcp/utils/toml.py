"""Utilities for working with TOML files while preserving formatting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple, Union

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.items import Item

from .errors import ConfigurationError
from .paths import resolve_repo_path

_PathLike = Union[str, Path]
_Token = Union[str, int]


def _unwrap(value: object) -> object:
    """Return a plain Python representation of a tomlkit item."""

    if hasattr(value, "unwrap"):
        return value.unwrap()  # type: ignore[no-any-return]
    return value


@dataclass(frozen=True)
class TomlHandler:
    """TOML helper that supports dotted-path lookups and assignments."""

    path: Path

    def __init__(self, path: _PathLike):
        object.__setattr__(self, "path", resolve_repo_path(path))

    # ------------------------------------------------------------------
    # Reading helpers
    # ------------------------------------------------------------------
    def read_text(self) -> str:
        """Return the raw TOML file content."""

        try:
            return self.path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:  # pragma: no cover - defensive
            raise ConfigurationError(f"TOML file not found at {self.path}") from exc

    def read_document(self) -> TOMLDocument:
        """Parse the TOML document into a tomlkit structure."""

        return tomlkit.parse(self.read_text())

    def get_value(self, dotted_path: str) -> object:
        """Retrieve a value using dotted path and index notation."""

        tokens = self._parse_path(dotted_path)
        document = self.read_document()
        return _unwrap(self._resolve_tokens(document, tokens))

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------
    def write_document(self, document: TOMLDocument) -> None:
        """Persist the provided TOML document with a backup."""

        backup_path = self.path.with_suffix(self.path.suffix + ".backup")

        if self.path.exists():
            backup_path.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(tomlkit.dumps(document), encoding="utf-8")

    def set_value(self, dotted_path: str, value: object) -> Tuple[object, object]:
        """Assign a value using dotted path syntax.

        Args:
            dotted_path: Path to the value (e.g. ``settings.general.tip_reuse``).
            value: Python value or tomlkit Item to assign.

        Returns:
            Tuple of (old_value, new_value) with plain Python representations.
        """

        tokens = self._parse_path(dotted_path)
        document = self.read_document()
        old_item, new_item = self._set_value(document, tokens, value)
        self.write_document(document)
        return _unwrap(old_item), _unwrap(new_item)

    def set_values(self, updates: Sequence[Tuple[str, object]]) -> List[Tuple[str, object, object]]:
        """Apply multiple updates in a single write operation."""

        document = self.read_document()
        results: List[Tuple[str, object, object]] = []

        for dotted_path, value in updates:
            tokens = self._parse_path(dotted_path)
            old_item, new_item = self._set_value(document, tokens, value)
            results.append((dotted_path, _unwrap(old_item), _unwrap(new_item)))

        self.write_document(document)
        return results

    def append_array_item(self, dotted_path: str, value: object) -> object:
        """Append a value to an array while preserving formatting."""

        tokens = self._parse_path(dotted_path)
        document = self.read_document()
        array = self._resolve_tokens(document, tokens)

        if not isinstance(array, list):
            raise ConfigurationError(f"Target path '{dotted_path}' is not an array")

        item = value if isinstance(value, Item) else tomlkit.item(value)
        array.append(item)

        self.write_document(document)
        return _unwrap(item)

    def _set_value(self, document: TOMLDocument, tokens: Sequence[_Token], value: object) -> Tuple[Item, Item]:
        parent, final_token = self._resolve_parent(document, tokens)
        new_item = value if isinstance(value, Item) else tomlkit.item(value)

        try:
            if isinstance(final_token, int):
                old_item = parent[final_token]  # type: ignore[index]
                parent[final_token] = new_item  # type: ignore[index]
            else:
                old_item = parent[final_token]  # type: ignore[index]
                parent[final_token] = new_item  # type: ignore[index]
        except (KeyError, IndexError, TypeError) as exc:
            raise ConfigurationError(f"TOML path segment '{final_token}' not found") from exc

        return old_item, new_item

    # ------------------------------------------------------------------
    # Path parsing helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_path(dotted_path: str) -> List[_Token]:
        if not dotted_path:
            raise ConfigurationError("Empty TOML path provided")

        tokens: List[_Token] = []
        for component in dotted_path.split("."):
            tokens.extend(TomlHandler._parse_component(component))
        return tokens

    @staticmethod
    def _parse_component(component: str) -> Iterable[_Token]:
        buffer = component
        while buffer:
            if "[" in buffer:
                field, rest = buffer.split("[", 1)
                if field:
                    yield field
                index_str, remainder = rest.split("]", 1)
                if not index_str.isdigit():
                    raise ConfigurationError(f"Invalid array index '{index_str}' in TOML path")
                yield int(index_str)
                buffer = remainder
            else:
                yield buffer
                buffer = ""

    @staticmethod
    def _resolve_tokens(document: object, tokens: Sequence[_Token]) -> object:
        current: object = document
        for token in tokens:
            try:
                if isinstance(token, int):
                    current = current[token]  # type: ignore[index]
                else:
                    current = current[token]  # type: ignore[index]
            except (KeyError, IndexError, TypeError) as exc:
                raise ConfigurationError(f"TOML path segment '{token}' not found") from exc
        return current

    @staticmethod
    def _resolve_parent(document: object, tokens: Sequence[_Token]) -> Tuple[object, _Token]:
        if not tokens:
            raise ConfigurationError("Empty TOML path provided")

        if len(tokens) == 1:
            return document, tokens[0]

        parent = TomlHandler._resolve_tokens(document, tokens[:-1])
        return parent, tokens[-1]


__all__ = ["TomlHandler"]
