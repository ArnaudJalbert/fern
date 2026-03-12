from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True, kw_only=True)
class Page:
    id: int
    title: str
    content: str
