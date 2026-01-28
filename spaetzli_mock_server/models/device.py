"""Device model for registered premium devices."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Device:
    """Represents a registered premium device."""
    device_identifier: str
    device_name: str
    platform: str
    user: str = "default"
    created_at: int = field(default_factory=lambda: int(time.time()))
    last_seen_at: int = field(default_factory=lambda: int(time.time()))
    
    def to_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "device_identifier": self.device_identifier,
            "device_name": self.device_name,
            "platform": self.platform,
            "user": self.user,
            "createdAt": self.created_at,
            "lastSeenAt": self.last_seen_at,
        }
