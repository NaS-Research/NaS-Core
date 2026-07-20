from pathlib import Path
from typing import Any

import yaml
from pydantic import TypeAdapter, ValidationError

from nas_core.domain.datasets import SourceRegistration
from nas_core.governance.exceptions import SourceNotFoundError

_SOURCE_LIST_ADAPTER = TypeAdapter(list[SourceRegistration])


class SourceRegistry:
    def __init__(self, sources: list[SourceRegistration]) -> None:
        source_map = {source.source_id: source for source in sources}
        if len(source_map) != len(sources):
            raise ValueError("Source registry contains duplicate source IDs")
        self._sources = source_map

    @classmethod
    def from_yaml(cls, path: Path) -> "SourceRegistry":
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or "sources" not in raw:
            raise ValueError("Source registry must contain a top-level 'sources' list")
        try:
            sources = _SOURCE_LIST_ADAPTER.validate_python(raw["sources"])
        except ValidationError as error:
            raise ValueError(f"Invalid source registry: {error}") from error
        return cls(sources)

    def get(self, source_id: str) -> SourceRegistration:
        try:
            return self._sources[source_id]
        except KeyError as error:
            raise SourceNotFoundError(f"Source is not registered: {source_id}") from error

    def list(self) -> tuple[SourceRegistration, ...]:
        return tuple(self._sources.values())
