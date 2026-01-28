"""Main API routes (/api/1/)."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from ..auth import require_auth
from ..config import config
from ..storage import storage
from ..models import Watcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/1")


def check_auth(api_key: Optional[str]) -> None:
    """Verify authentication or raise 401."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API KEY signature mismatch")


@router.get("/last_data_metadata")
async def get_last_data_metadata(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """
    Get metadata about the last uploaded database.
    This endpoint is also used to verify premium status.
    """
    check_auth(api_key)
    
    # Get user from request (simplified - in real impl would decode from API key)
    user = "default"
    
    metadata = storage.get_backup_metadata(user)
    if metadata:
        return metadata.to_dict()
    
    # Return empty metadata if no backup exists
    # This still indicates valid premium (no error)
    return {
        "upload_ts": 0,
        "last_modify_ts": 0,
        "data_hash": "",
        "data_size": 0,
    }


@router.get("/statistics_rendererv2")
async def get_statistics_renderer(
    request: Request,
    version: Optional[int] = None,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """
    Get the premium statistics renderer component.
    
    This returns JavaScript code that gets injected into the frontend.
    In mock mode, we return a minimal stub that satisfies the loader.
    """
    check_auth(api_key)
    
    # Check if we have real premium components
    components_file = config.data_dir / "premium_components.js"
    if components_file.exists():
        js_code = components_file.read_text()
    else:
        # Return stub that creates empty premium components
        js_code = """
// Spaetzli Mock Premium Components
(function() {
    const components = {
        PremiumStatistics: {
            template: '<div class="premium-mock">Premium Statistics (Mock)</div>',
            name: 'PremiumStatistics'
        },
        EthStaking: {
            template: '<div class="premium-mock">ETH Staking View (Mock)</div>',
            name: 'EthStaking'
        },
        AssetAmountAndValueOverTime: {
            template: '<div class="premium-mock">Asset Chart (Mock)</div>',
            name: 'AssetAmountAndValueOverTime'
        },
        ThemeManager: {
            template: '<div></div>',
            name: 'ThemeManager'
        }
    };
    
    const PremiumComponents = {
        install(app) {
            Object.entries(components).forEach(([name, component]) => {
                app.component(name, component);
            });
        },
        ...components
    };
    
    window.PremiumComponents = PremiumComponents;
})();
"""
    
    return {"data": js_code}


# ========== Watchers ==========

@router.get("/watchers")
async def get_watchers(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Get all watchers."""
    check_auth(api_key)
    
    watchers = storage.get_watchers()
    return {"watchers": [w.to_dict() for w in watchers]}


@router.put("/watchers")
async def add_watchers(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Add new watchers."""
    check_auth(api_key)
    
    body = await request.json()
    watchers_data = body.get("watchers", [])
    
    created = []
    for w_data in watchers_data:
        watcher = Watcher(
            watcher_type=w_data.get("type", ""),
            args=w_data.get("args", {}),
        )
        storage.add_watcher(watcher)
        created.append(watcher.to_dict())
    
    return {"watchers": created}


@router.patch("/watchers")
async def edit_watchers(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Edit existing watchers."""
    check_auth(api_key)
    
    body = await request.json()
    watchers_data = body.get("watchers", [])
    
    updated = []
    for w_data in watchers_data:
        identifier = w_data.get("identifier")
        if identifier:
            watcher = storage.update_watcher(identifier, w_data.get("args", {}))
            if watcher:
                updated.append(watcher.to_dict())
    
    return {"watchers": updated}


@router.delete("/watchers")
async def delete_watchers(
    request: Request,
    api_key: Optional[str] = Header(None, alias="API-KEY"),
):
    """Delete watchers by identifier."""
    check_auth(api_key)
    
    body = await request.json()
    watcher_ids = body.get("watchers", [])
    
    for watcher_id in watcher_ids:
        storage.delete_watcher(watcher_id)
    
    # Return remaining watchers
    watchers = storage.get_watchers()
    return {"watchers": [w.to_dict() for w in watchers]}


# ========== Usage Analytics (Optional) ==========

@router.post("/usage_analytics")
async def usage_analytics(request: Request):
    """Accept and ignore usage analytics (no auth required)."""
    # Just accept and do nothing - this is anonymous telemetry
    return {"success": True}
