from dataclasses import dataclass, field
from typing import Any

@dataclass
class Version:
    id: str
    type: str = "unknown"
    source: str = "unknown"
    url: str | None = None
    release_time: str | None = None
    sha1: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
