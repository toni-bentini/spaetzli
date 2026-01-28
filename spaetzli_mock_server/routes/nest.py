"""Nest API routes (/nest/1/) - devices, backups, limits."""

import logging
import time
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.responses import JSONResponse

from ..auth import require_auth
from ..config import config
from ..storage import storage
from ..models import Device, BackupMetadata

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/nest/1")


def check_auth(api_key: Optional[str]) -> None:
    """Verify authentication or raise 401."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API KEY signature mismatch")


# ========== Limits ==========

@router.get("/limits")
async def get_limits(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Get user limits and capabilities."""
    check_auth(api_key)
    
    return {
        "limit_of_devices": config.limits.limit_of_devices,
        "pnl_events_limit": config.limits.pnl_events_limit,
        "max_backup_size_mb": config.limits.max_backup_size_mb,
        "history_events_limit": config.limits.history_events_limit,
        "reports_lookup_limit": config.limits.reports_lookup_limit,
        "eth_staked_limit": config.limits.eth_staked_limit,
        "eth_staking_view": config.capabilities.eth_staking_view,
        "graphs_view": config.capabilities.graphs_view,
        "event_analysis_view": config.capabilities.event_analysis_view,
    }


# ========== Devices ==========

@router.get("/devices")
async def get_devices(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Get list of registered devices."""
    check_auth(api_key)
    
    devices = storage.get_devices()
    return {
        "devices": [d.to_dict() for d in devices],
        "limit": config.limits.limit_of_devices,
    }


@router.post("/devices/check")
async def check_device(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Check if a device is registered."""
    check_auth(api_key)
    
    body = await request.json()
    device_id = body.get("device_identifier", "")
    
    if storage.device_exists(device_id):
        return Response(status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Device not found")


@router.put("/devices")
async def register_device(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Register a new device."""
    check_auth(api_key)
    
    body = await request.json()
    device_id = body.get("device_identifier", "")
    device_name = body.get("device_name", "Unknown Device")
    platform = body.get("platform", "Unknown")
    
    # Check if device already exists
    if storage.device_exists(device_id):
        return Response(status_code=409)  # Conflict - already exists
    
    device = Device(
        device_identifier=device_id,
        device_name=device_name,
        platform=platform,
    )
    
    if storage.add_device(device):
        return Response(status_code=201)
    else:
        # Device limit reached
        raise HTTPException(
            status_code=422,
            detail=f"Device limit ({config.limits.limit_of_devices}) exceeded"
        )


@router.patch("/devices")
async def edit_device(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Edit a device's name."""
    check_auth(api_key)
    
    body = await request.json()
    device_id = body.get("device_identifier", "")
    device_name = body.get("device_name", "")
    
    if not device_name:
        raise HTTPException(status_code=400, detail="device_name required")
    
    if storage.update_device(device_id, device_name):
        return Response(status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Device not found")


@router.delete("/devices")
async def delete_device(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Delete a registered device."""
    check_auth(api_key)
    
    body = await request.json()
    device_id = body.get("device_identifier", "")
    
    if storage.delete_device(device_id):
        return Response(status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Device not found")


# ========== Backup ==========

@router.get("/backup")
async def get_backup(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Download the stored database backup."""
    check_auth(api_key)
    
    user = "default"
    data = storage.get_backup_data(user)
    
    if data is None:
        raise HTTPException(status_code=404, detail="No backup found")
    
    return Response(
        content=data,
        media_type="application/octet-stream",
    )


@router.post("/backup/range")
async def upload_backup_chunk(
    request: Request,
    chunk_data: UploadFile = File(...),
    file_hash: str = Form(...),
    last_modify_ts: int = Form(...),
    compression: str = Form("zlib"),
    total_size: int = Form(...),
    upload_id: Optional[str] = Form(None),
    api_key: Optional[str] = Header(None, alias="API-KEY"),
    content_range: Optional[str] = Header(None, alias="Content-Range"),
):
    """
    Upload a database backup chunk.
    
    Supports chunked uploads for large files.
    Content-Range header format: bytes {start}-{end}/{total}
    """
    check_auth(api_key)
    
    user = "default"
    chunk_bytes = await chunk_data.read()
    
    # Parse content range
    is_first_chunk = upload_id is None
    is_complete = True
    
    if content_range:
        # Parse "bytes 0-999/1000" format
        try:
            range_spec = content_range.replace("bytes ", "")
            range_part, total_part = range_spec.split("/")
            start, end = map(int, range_part.split("-"))
            total = int(total_part)
            is_complete = (end + 1) >= total
        except:
            pass
    
    if is_first_chunk and not is_complete:
        # Start chunked upload
        new_upload_id = str(uuid4())
        storage.start_chunked_upload(new_upload_id, total_size, user)
        storage.add_chunk(new_upload_id, chunk_bytes, 0)
        return JSONResponse(
            status_code=206,  # Partial Content
            content={"upload_id": new_upload_id}
        )
    
    if upload_id and not is_complete:
        # Continue chunked upload
        if content_range:
            try:
                range_spec = content_range.replace("bytes ", "")
                range_part, _ = range_spec.split("/")
                start, _ = map(int, range_part.split("-"))
                storage.add_chunk(upload_id, chunk_bytes, start)
            except:
                storage.add_chunk(upload_id, chunk_bytes, 0)
        else:
            storage.add_chunk(upload_id, chunk_bytes, 0)
        
        return JSONResponse(
            status_code=206,
            content={"upload_id": upload_id}
        )
    
    # Final chunk or single-chunk upload
    if upload_id:
        # Finalize chunked upload
        if content_range:
            try:
                range_spec = content_range.replace("bytes ", "")
                range_part, _ = range_spec.split("/")
                start, _ = map(int, range_part.split("-"))
                storage.add_chunk(upload_id, chunk_bytes, start)
            except:
                storage.add_chunk(upload_id, chunk_bytes, 0)
        else:
            storage.add_chunk(upload_id, chunk_bytes, 0)
        
        metadata = storage.finalize_upload(upload_id, last_modify_ts)
    else:
        # Single chunk upload (small file)
        metadata = storage.store_backup(user, chunk_bytes, last_modify_ts, compression)
    
    if metadata:
        return JSONResponse(status_code=200, content=metadata.to_dict())
    else:
        raise HTTPException(status_code=500, detail="Failed to store backup")
