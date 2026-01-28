"""Basic tests for the mock server."""

import pytest
from fastapi.testclient import TestClient

from spaetzli_mock_server.app import app
from spaetzli_mock_server.config import config
from spaetzli_mock_server.storage import storage
from spaetzli_mock_server.models import Device, Watcher


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_storage():
    """Reset storage between tests."""
    storage._devices.clear()
    storage._watchers.clear()
    storage._backups.clear()
    storage._backup_data.clear()
    yield


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "spaetzli-mock-premium"
    
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestApiEndpoints:
    """Test /api/1/ endpoints."""
    
    def test_last_data_metadata_requires_auth(self, client):
        response = client.get("/api/1/last_data_metadata")
        assert response.status_code == 401
    
    def test_last_data_metadata_with_auth(self, client):
        response = client.get(
            "/api/1/last_data_metadata",
            headers={"API-KEY": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "upload_ts" in data
        assert "data_hash" in data
    
    def test_statistics_renderer(self, client):
        response = client.get(
            "/api/1/statistics_rendererv2",
            headers={"API-KEY": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "PremiumComponents" in data["data"]
    
    def test_watchers_crud(self, client):
        headers = {"API-KEY": "test-key"}
        
        # Get empty watchers
        response = client.get("/api/1/watchers", headers=headers)
        assert response.status_code == 200
        assert response.json()["watchers"] == []
        
        # Add watcher
        response = client.put(
            "/api/1/watchers",
            headers=headers,
            json={"watchers": [{"type": "test_watcher", "args": {"threshold": 100}}]}
        )
        assert response.status_code == 200
        watchers = response.json()["watchers"]
        assert len(watchers) == 1
        watcher_id = watchers[0]["identifier"]
        
        # Get watchers
        response = client.get("/api/1/watchers", headers=headers)
        assert len(response.json()["watchers"]) == 1
        
        # Delete watcher
        response = client.request(
            "DELETE",
            "/api/1/watchers",
            headers=headers,
            json={"watchers": [watcher_id]}
        )
        assert response.status_code == 200
        assert response.json()["watchers"] == []


class TestNestEndpoints:
    """Test /nest/1/ endpoints."""
    
    def test_limits(self, client):
        response = client.get(
            "/nest/1/limits",
            headers={"API-KEY": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["history_events_limit"] == config.limits.history_events_limit
        assert data["graphs_view"] == config.capabilities.graphs_view
    
    def test_device_lifecycle(self, client):
        headers = {"API-KEY": "test-key"}
        device_id = "test-device-abc"
        
        # Check device doesn't exist
        response = client.post(
            "/nest/1/devices/check",
            headers=headers,
            json={"device_identifier": device_id}
        )
        assert response.status_code == 404
        
        # Register device
        response = client.put(
            "/nest/1/devices",
            headers=headers,
            json={
                "device_identifier": device_id,
                "device_name": "Test Device",
                "platform": "Linux"
            }
        )
        assert response.status_code == 201
        
        # Check device exists
        response = client.post(
            "/nest/1/devices/check",
            headers=headers,
            json={"device_identifier": device_id}
        )
        assert response.status_code == 200
        
        # Get devices
        response = client.get("/nest/1/devices", headers=headers)
        assert response.status_code == 200
        devices = response.json()["devices"]
        assert len(devices) == 1
        assert devices[0]["device_identifier"] == device_id
        
        # Edit device
        response = client.patch(
            "/nest/1/devices",
            headers=headers,
            json={"device_identifier": device_id, "device_name": "New Name"}
        )
        assert response.status_code == 200
        
        # Delete device
        response = client.request(
            "DELETE",
            "/nest/1/devices",
            headers=headers,
            json={"device_identifier": device_id}
        )
        assert response.status_code == 200
        
        # Verify deleted
        response = client.get("/nest/1/devices", headers=headers)
        assert len(response.json()["devices"]) == 0


class TestStorage:
    """Test storage layer."""
    
    def test_device_limit(self):
        """Test that device limit is enforced."""
        original_limit = config.limits.limit_of_devices
        config.limits.limit_of_devices = 2
        
        try:
            # Add up to limit
            for i in range(2):
                device = Device(
                    device_identifier=f"device-{i}",
                    device_name=f"Device {i}",
                    platform="Test"
                )
                assert storage.add_device(device) is True
            
            # Try to exceed limit
            device = Device(
                device_identifier="device-extra",
                device_name="Extra Device",
                platform="Test"
            )
            assert storage.add_device(device) is False
        finally:
            config.limits.limit_of_devices = original_limit
    
    def test_backup_storage(self):
        """Test backup storage and retrieval."""
        test_data = b"encrypted database content"
        
        metadata = storage.store_backup(
            user="test-user",
            data=test_data,
            last_modify_ts=1234567890
        )
        
        assert metadata.data_size == len(test_data)
        assert metadata.last_modify_ts == 1234567890
        
        retrieved = storage.get_backup_data("test-user")
        assert retrieved == test_data
