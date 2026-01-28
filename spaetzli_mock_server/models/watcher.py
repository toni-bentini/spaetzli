"""Watcher model for price alerts."""

from dataclasses import dataclass, field
from typing import Any, Dict
from uuid import uuid4


@dataclass
class Watcher:
    """Represents a premium watcher/alert."""
    identifier: str = field(default_factory=lambda: str(uuid4()))
    watcher_type: str = ""  # e.g., "makervault_collateralization_ratio"
    args: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "identifier": self.identifier,
            "type": self.watcher_type,
            "args": self.args,
        }
