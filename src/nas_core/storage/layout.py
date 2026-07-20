import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar


class InvalidDataRootError(ValueError):
    """Raised when a configured data root is absent, unsafe, or incomplete."""


@dataclass(frozen=True, slots=True)
class DataLayout:
    root: Path

    MARKER_FILE: ClassVar[str] = ".nas-core-data-root.json"
    SCHEMA_VERSION: ClassVar[int] = 1
    REQUIRED_DIRECTORIES: ClassVar[tuple[str, ...]] = (
        "object-store",
        "working",
        "exports",
        "quarantine",
        "database-backups",
        "audit",
    )

    def initialize(self) -> None:
        root = self._safe_absolute_root()
        root.mkdir(parents=True, exist_ok=True)
        for directory in self.REQUIRED_DIRECTORIES:
            (root / directory).mkdir(exist_ok=True)

        marker = root / self.MARKER_FILE
        if not marker.exists():
            marker.write_text(
                json.dumps(
                    {
                        "schema_version": self.SCHEMA_VERSION,
                        "kind": "nas-core-data-root",
                        "created_at": datetime.now(UTC).isoformat(),
                        "object_store_prefixes": [
                            "raw/",
                            "normalized/",
                            "analysis-ready/",
                            "artifacts/",
                            "releases/",
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        self.validate()

    def validate(self) -> None:
        root = self._safe_absolute_root()
        if not root.is_dir():
            raise InvalidDataRootError(f"Data root does not exist: {root}")

        marker = root / self.MARKER_FILE
        if not marker.is_file():
            raise InvalidDataRootError(f"Data-root marker is missing: {marker}")
        try:
            metadata = json.loads(marker.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise InvalidDataRootError(f"Data-root marker is invalid: {marker}") from error

        if metadata.get("kind") != "nas-core-data-root":
            raise InvalidDataRootError("Configured path is not a NaS Core data root")
        if metadata.get("schema_version") != self.SCHEMA_VERSION:
            raise InvalidDataRootError("Unsupported data-root schema version")

        missing = [
            directory for directory in self.REQUIRED_DIRECTORIES if not (root / directory).is_dir()
        ]
        if missing:
            raise InvalidDataRootError(
                f"Data root is missing required directories: {', '.join(missing)}"
            )

    def _safe_absolute_root(self) -> Path:
        root = self.root.expanduser().resolve()
        prohibited = {Path("/"), Path.home().resolve(), Path("/Volumes")}
        if not root.is_absolute() or root in prohibited or len(root.parts) < 3:
            raise InvalidDataRootError(f"Unsafe data-root path: {root}")
        return root
