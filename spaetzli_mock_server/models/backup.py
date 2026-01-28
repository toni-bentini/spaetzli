"""Backup metadata model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib


@dataclass
class BackupMetadata:
    """Metadata for a stored database backup."""
    user: str
    upload_ts: int  # Unix timestamp
    last_modify_ts: int  # Unix timestamp
    data_hash: str
    data_size: int
    compression: str = "zlib"
    file_path: Optional[str] = None
    
    @classmethod
    def create_empty(cls) -> "BackupMetadata":
        """Create metadata indicating no backup exists."""
        return cls(
            user="",
            upload_ts=0,
            last_modify_ts=0,
            data_hash="",
            data_size=0,
        )
    
    def to_dict(self) -> dict:
        """Convert to API response format."""
        return {
            "upload_ts": self.upload_ts,
            "last_modify_ts": self.last_modify_ts,
            "data_hash": self.data_hash,
            "data_size": self.data_size,
        }
