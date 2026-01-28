"""In-memory storage for mock server data."""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock

from .models import Device, BackupMetadata, Watcher
from .config import config


class Storage:
    """Thread-safe in-memory storage with optional file persistence."""
    
    def __init__(self):
        self._lock = Lock()
        self._devices: Dict[str, Device] = {}
        self._backups: Dict[str, BackupMetadata] = {}
        self._watchers: Dict[str, Watcher] = {}
        self._backup_data: Dict[str, bytes] = {}  # user -> encrypted data
        self._pending_uploads: Dict[str, dict] = {}  # upload_id -> chunk info
    
    # ========== Device Methods ==========
    
    def get_devices(self, user: str = "default") -> List[Device]:
        """Get all devices for a user."""
        with self._lock:
            return [d for d in self._devices.values() if d.user == user]
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """Get a specific device."""
        with self._lock:
            return self._devices.get(device_id)
    
    def device_exists(self, device_id: str) -> bool:
        """Check if a device exists."""
        with self._lock:
            return device_id in self._devices
    
    def add_device(self, device: Device) -> bool:
        """Add a new device. Returns False if device limit reached."""
        with self._lock:
            user_devices = [d for d in self._devices.values() if d.user == device.user]
            if len(user_devices) >= config.limits.limit_of_devices:
                return False
            self._devices[device.device_identifier] = device
            return True
    
    def update_device(self, device_id: str, device_name: str) -> bool:
        """Update a device name."""
        with self._lock:
            if device_id not in self._devices:
                return False
            self._devices[device_id].device_name = device_name
            return True
    
    def delete_device(self, device_id: str) -> bool:
        """Delete a device."""
        with self._lock:
            if device_id not in self._devices:
                return False
            del self._devices[device_id]
            return True
    
    # ========== Backup Methods ==========
    
    def get_backup_metadata(self, user: str = "default") -> Optional[BackupMetadata]:
        """Get backup metadata for a user."""
        with self._lock:
            return self._backups.get(user)
    
    def get_backup_data(self, user: str = "default") -> Optional[bytes]:
        """Get the actual backup data."""
        with self._lock:
            return self._backup_data.get(user)
    
    def store_backup(
        self,
        user: str,
        data: bytes,
        last_modify_ts: int,
        compression: str = "zlib"
    ) -> BackupMetadata:
        """Store a backup and return metadata."""
        data_hash = hashlib.sha256(data).hexdigest()
        metadata = BackupMetadata(
            user=user,
            upload_ts=int(time.time()),
            last_modify_ts=last_modify_ts,
            data_hash=data_hash,
            data_size=len(data),
            compression=compression,
        )
        
        with self._lock:
            self._backups[user] = metadata
            self._backup_data[user] = data
            
            # Optionally persist to disk
            backup_file = config.backups_dir / f"{user}_backup.bin"
            backup_file.write_bytes(data)
            
            meta_file = config.backups_dir / f"{user}_metadata.json"
            meta_file.write_text(json.dumps(metadata.to_dict()))
        
        return metadata
    
    # ========== Chunked Upload Methods ==========
    
    def start_chunked_upload(self, upload_id: str, total_size: int, user: str = "default"):
        """Initialize a chunked upload session."""
        with self._lock:
            self._pending_uploads[upload_id] = {
                "user": user,
                "total_size": total_size,
                "received_size": 0,
                "chunks": [],
            }
    
    def add_chunk(self, upload_id: str, chunk: bytes, offset: int) -> bool:
        """Add a chunk to a pending upload."""
        with self._lock:
            if upload_id not in self._pending_uploads:
                return False
            upload = self._pending_uploads[upload_id]
            upload["chunks"].append((offset, chunk))
            upload["received_size"] += len(chunk)
            return True
    
    def finalize_upload(self, upload_id: str, last_modify_ts: int) -> Optional[BackupMetadata]:
        """Finalize a chunked upload and store the complete backup."""
        with self._lock:
            if upload_id not in self._pending_uploads:
                return None
            
            upload = self._pending_uploads.pop(upload_id)
            
            # Reassemble chunks in order
            chunks = sorted(upload["chunks"], key=lambda x: x[0])
            data = b"".join(chunk for _, chunk in chunks)
            
        # Store the complete backup (outside lock to avoid long holds)
        return self.store_backup(
            user=upload["user"],
            data=data,
            last_modify_ts=last_modify_ts,
        )
    
    # ========== Watcher Methods ==========
    
    def get_watchers(self, user: str = "default") -> List[Watcher]:
        """Get all watchers."""
        with self._lock:
            return list(self._watchers.values())
    
    def add_watcher(self, watcher: Watcher) -> Watcher:
        """Add a new watcher."""
        with self._lock:
            self._watchers[watcher.identifier] = watcher
            return watcher
    
    def update_watcher(self, identifier: str, args: dict) -> Optional[Watcher]:
        """Update a watcher's args."""
        with self._lock:
            if identifier not in self._watchers:
                return None
            self._watchers[identifier].args = args
            return self._watchers[identifier]
    
    def delete_watcher(self, identifier: str) -> bool:
        """Delete a watcher."""
        with self._lock:
            if identifier not in self._watchers:
                return False
            del self._watchers[identifier]
            return True


# Global storage instance
storage = Storage()
