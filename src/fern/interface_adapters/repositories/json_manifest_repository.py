"""Persist and load Manifest as JSON in a database directory."""

import json
from pathlib import Path

from fern.domain.entities import Manifest, Property, PropertyType
from fern.domain.repositories.manifest_repository import ManifestRepository

MANIFEST_FILENAME = "manifest.json"


def _property_from_dict(d: dict) -> Property:
    raw = d.get("type", "boolean")
    ptype = PropertyType.from_key(raw)
    return Property(id=str(d["id"]), name=str(d["name"]), type=ptype)


def _property_to_dict(p: Property) -> dict:
    return {"id": p.id, "name": p.name, "type": p.type.key()}


class JsonManifestRepository(ManifestRepository):
    """Read/write manifest from manifest.json in the given directory."""

    def __init__(self, database_dir: Path | str) -> None:
        self._dir = Path(database_dir)

    def get(self) -> Manifest:
        path = self._dir / MANIFEST_FILENAME
        if not path.is_file():
            return Manifest(properties=[])
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return Manifest(properties=[])
        props = data.get("properties") or []
        return Manifest(
            properties=[
                _property_from_dict(p)
                for p in props
                if isinstance(p, dict) and "id" in p
            ]
        )

    def save(self, manifest: Manifest) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / MANIFEST_FILENAME
        data = {"properties": [_property_to_dict(p) for p in manifest.properties]}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
