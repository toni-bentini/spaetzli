# Spaetzli - Rotki Premium API Mock Plan

## Overview

This document outlines the findings from analyzing Rotki's premium system and provides a plan to create a mock premium API server that enables all premium features locally.

---

## 1. Premium Features Analysis

### 1.1 Numerical Limits (Free vs Premium)

| Limit Type | Free Limit | Premium | Code Location |
|------------|------------|---------|---------------|
| History Events | 1,000 | Configurable | `rotkehlchen/constants/limits.py` |
| User Notes | 10 | Configurable | `rotkehlchen/constants/limits.py` |
| P&L Events | 1,000 | Configurable | `rotkehlchen/accounting/constants.py` |
| Reports Lookup | 20 | Configurable | `rotkehlchen/accounting/constants.py` |
| ETH Staked | 128 ETH (4 validators) | Configurable | `rotkehlchen/premium/premium.py` |

### 1.2 Boolean Capabilities

```python
PREMIUM_CAPABILITIES_KEYS = (
    'eth_staking_view',     # ETH staking dashboard
    'graphs_view',          # Premium graphs/charts
    'event_analysis_view',  # Event analysis features
)
```

### 1.3 Premium-Only Features

1. **Cloud Database Backup/Sync** - Upload/download encrypted database
2. **Device Management** - Register/manage multiple devices  
3. **Watchers** - Price/threshold alerts
4. **Premium UI Components** - Vue components loaded via `statistics_rendererv2`
5. **Higher/Unlimited Limits** - All numerical limits above

---

## 2. External API Endpoints (rotki.com)

### 2.1 Base URLs

```python
# Production
rotki_api  = 'https://rotki.com/api/1/'
rotki_nest = 'https://rotki.com/nest/1/'

# Staging (when ROTKI_API_ENVIRONMENT=staging)
rotki_api  = 'https://staging.rotki.com/api/1/'
rotki_nest = 'https://staging.rotki.com/nest/1/'
```

### 2.2 Main API Endpoints (`/api/1/`)

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `last_data_metadata` | GET | Check premium status, get remote DB metadata | Yes |
| `statistics_rendererv2` | GET | Download premium Vue components (JS bundle) | Yes |
| `watchers` | GET | List watchers | Yes |
| `watchers` | PUT | Add watchers | Yes |
| `watchers` | PATCH | Edit watchers | Yes |
| `watchers` | DELETE | Delete watchers | Yes |
| `usage_analytics` | POST | Anonymous usage stats | No |

### 2.3 Nest API Endpoints (`/nest/1/`)

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `backup` | GET | Download encrypted database backup | Yes |
| `backup/range` | POST | Upload database in chunks | Yes |
| `devices` | GET | List registered devices | Yes |
| `devices` | PUT | Register new device | Yes |
| `devices` | PATCH | Edit device name | Yes |
| `devices` | DELETE | Delete device | Yes |
| `devices/check` | POST | Check if device is registered | Yes |
| `limits` | GET | Get user limits and capabilities | Yes |

---

## 3. Authentication System

### 3.1 Request Signing

```python
# Headers required:
# - API-KEY: <api_key>
# - API-SIGN: base64(hmac_sha512(message, api_secret))

# Signature computation:
urlpath = f'/api/{version}/{method}'  # or /nest/{version}/{method}
req['nonce'] = int(1000 * time.time())
post_data = urlencode(req)
hashable = post_data.encode()

# For nest endpoints:
message = urlpath.encode() + hashlib.sha256(hashable).hexdigest().encode()
# For api endpoints:
message = urlpath.encode() + hashlib.sha256(hashable).digest()

signature = hmac.new(api_secret, message, hashlib.sha512)
# Header: API-SIGN = base64.b64encode(signature.digest())
```

### 3.2 Credential Format

```python
# API Key: Base64 encoded string
VALID_PREMIUM_KEY = 'kWT/MaPHwM2W1KUEl2aXtkKG6wJfMW9KxI7SSerI6/QzchC45/GebPV9xYZy7f+VKBeh5nDRBJBCYn7WofMO4Q=='

# API Secret: Base64 encoded bytes (decoded before use)
VALID_PREMIUM_SECRET = 'TEF5dFFrOFcwSXNrM2p1aDdHZmlndFRoMTZQRWJhU2dacTdscUZSeHZTRmJLRm5ZaVRlV2NYU...'
```

---

## 4. Response Formats

### 4.1 `last_data_metadata` Response

```json
{
  "upload_ts": 1703275200,
  "last_modify_ts": 1703275200,
  "data_hash": "abc123...",
  "data_size": 1048576
}
```

### 4.2 `limits` Response

```json
{
  "limit_of_devices": 10,
  "pnl_events_limit": 1000000,
  "max_backup_size_mb": 500,
  "history_events_limit": 1000000,
  "reports_lookup_limit": 1000,
  "eth_staked_limit": 32000,
  "eth_staking_view": true,
  "graphs_view": true,
  "event_analysis_view": true
}
```

### 4.3 `devices` Response

```json
{
  "devices": [
    {
      "device_name": "My Desktop",
      "user": "username",
      "device_identifier": "abc123..."
    }
  ],
  "limit": 10
}
```

### 4.4 `statistics_rendererv2` Response

```json
{
  "data": "/* JavaScript code for premium Vue components */..."
}
```

### 4.5 `watchers` Response

```json
{
  "watchers": [
    {
      "identifier": "watcher-uuid",
      "type": "makervault_collateralization_ratio",
      "args": {"vault_id": "123", "ratio": "150%"}
    }
  ]
}
```

---

## 5. Mock Server Implementation Plan

### 5.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Mock Premium Server                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   /api/1/   │  │  /nest/1/   │  │  Static Assets      │ │
│  │             │  │             │  │                     │ │
│  │ - metadata  │  │ - backup    │  │ - premium_components│ │
│  │ - renderer  │  │ - devices   │  │   (JS bundle)       │ │
│  │ - watchers  │  │ - limits    │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Rotki Application                         │
│  (configured to use mock server instead of rotki.com)       │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Implementation Options

#### Option A: Standalone Flask/FastAPI Server
- Run separate mock server on localhost
- Configure Rotki to use custom URLs via environment variables
- **Pros:** Clean separation, easy to test
- **Cons:** Extra process to manage

#### Option B: Hosts File + Local Server
- Add `127.0.0.1 rotki.com` to `/etc/hosts`
- Run HTTPS server with self-signed cert on port 443
- **Pros:** No Rotki code changes needed
- **Cons:** System-wide change, HTTPS complexity

#### Option C: Monkey-Patch Premium Module
- Patch `Premium` class URLs at runtime
- Override in `rotkehlchen_mock/__main__.py`
- **Pros:** Uses existing mock infrastructure
- **Cons:** More invasive changes

#### Option D: Environment Variable Configuration (Recommended)
- Rotki already supports staging via `ROTKI_API_ENVIRONMENT`
- Extend to support custom URLs
- **Pros:** Clean, no code changes to core

### 5.3 Recommended Approach: Option D + Standalone Server

1. **Create Mock Server** (`spaetzli_mock_server/`)
   - FastAPI-based for async support
   - Implement all endpoints from section 2
   - Optional signature validation (can be disabled)
   - In-memory or SQLite storage for devices/watchers/backups

2. **Environment Configuration**
   ```bash
   # Point Rotki to mock server
   export ROTKI_PREMIUM_API_URL="http://localhost:8080/api/1/"
   export ROTKI_PREMIUM_NEST_URL="http://localhost:8080/nest/1/"
   ```

3. **Premium Components**
   - Extract real premium components from legitimate subscription OR
   - Create stub components that enable UI without actual functionality OR
   - Return empty/minimal JS that satisfies the loader

---

## 6. Implementation Tasks

### Phase 1: Core Mock Server (Priority: High)

- [ ] **Task 1.1:** Create FastAPI project structure
- [ ] **Task 1.2:** Implement `/api/1/last_data_metadata` endpoint
- [ ] **Task 1.3:** Implement `/nest/1/limits` endpoint
- [ ] **Task 1.4:** Implement `/nest/1/devices/*` endpoints
- [ ] **Task 1.5:** Implement signature validation (optional)
- [ ] **Task 1.6:** Add configuration for limits/capabilities

### Phase 2: Database Sync (Priority: Medium)

- [ ] **Task 2.1:** Implement `/nest/1/backup` GET (download)
- [ ] **Task 2.2:** Implement `/nest/1/backup/range` POST (upload)
- [ ] **Task 2.3:** Add file storage for backups
- [ ] **Task 2.4:** Implement metadata tracking

### Phase 3: Advanced Features (Priority: Low)

- [ ] **Task 3.1:** Implement `/api/1/watchers` CRUD
- [ ] **Task 3.2:** Implement `/api/1/statistics_rendererv2`
- [ ] **Task 3.3:** Create or obtain premium UI components

### Phase 4: Integration (Priority: High)

- [ ] **Task 4.1:** Patch Rotki to use configurable URLs
- [ ] **Task 4.2:** Create startup script for mock server + Rotki
- [ ] **Task 4.3:** Test all premium features
- [ ] **Task 4.4:** Document usage

---

## 7. File Structure

```
spaetzli/
├── plan.md                          # This file
├── rotkehlchen/                     # Original Rotki code
├── rotkehlchen_mock/                # Existing mock server
└── spaetzli_mock_server/            # NEW: Premium mock server
    ├── __init__.py
    ├── __main__.py                  # Entry point
    ├── app.py                       # FastAPI app
    ├── config.py                    # Server configuration
    ├── auth.py                      # Signature validation
    ├── storage.py                   # Data persistence
    ├── routes/
    │   ├── __init__.py
    │   ├── api.py                   # /api/1/* routes
    │   └── nest.py                  # /nest/1/* routes
    ├── models/
    │   ├── __init__.py
    │   ├── device.py
    │   ├── backup.py
    │   └── watcher.py
    └── data/
        ├── backups/                 # Stored database backups
        └── premium_components.js    # Premium UI bundle (if available)
```

---

## 8. Quick Start (After Implementation)

```bash
# Terminal 1: Start mock premium server
cd spaetzli/spaetzli_mock_server
python -m spaetzli_mock_server --port 8080

# Terminal 2: Start Rotki with mock server
export ROTKI_PREMIUM_API_URL="http://localhost:8080/api/1/"
export ROTKI_PREMIUM_NEST_URL="http://localhost:8080/nest/1/"
cd spaetzli
python -m rotkehlchen --api-cors http://localhost:*

# In Rotki UI: Enter any API key/secret pair
# The mock server will accept any credentials and return premium status
```

---

## 9. Notes & Considerations

### 9.1 Legal/Ethical
- This is for **personal/educational use only**
- Do not distribute premium components if obtained from subscription
- Consider supporting the Rotki project if you use it regularly

### 9.2 Limitations
- Premium UI components (`statistics_rendererv2`) contain proprietary code
- Without real components, some UI features will fail gracefully
- Watchers won't actually send notifications (no external service)

### 9.3 Maintenance
- Rotki updates may change API contracts
- Monitor `rotkehlchen/premium/premium.py` for changes
- Version the mock server responses

---

## 10. References

- Premium module: `rotkehlchen/premium/premium.py`
- Premium sync: `rotkehlchen/premium/sync.py`
- Test utilities: `rotkehlchen/tests/utils/premium.py`
- API tests: `rotkehlchen/tests/api/test_premium.py`
- Frontend premium: `frontend/app/src/premium/`
- Existing mock: `rotkehlchen_mock/`
