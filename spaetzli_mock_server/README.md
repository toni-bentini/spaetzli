# Spaetzli Mock Premium Server

<p align="center">
  <img src="spaetzli-mascot.png" alt="Spaetzli Mascot" width="200">
</p>

<p align="center">
  <em>Meet Spätzli, your friendly premium companion! 🐦</em>
</p>

A mock server for Rotki premium features, allowing local development and testing without a premium subscription.

## Features

- ✅ Premium status verification (`/api/1/last_data_metadata`)
- ✅ User limits and capabilities (`/nest/1/limits`)
- ✅ Device management (`/nest/1/devices/*`)
- ✅ Database backup/sync (`/nest/1/backup`, `/nest/1/backup/range`)
- ✅ Watchers CRUD (`/api/1/watchers`)
- ✅ Premium components stub (`/api/1/statistics_rendererv2`)

## Installation

```bash
cd spaetzli_mock_server
pip install -r requirements.txt
```

## Usage

### Start the mock server

```bash
# From the spaetzli_mock_server directory
python -m spaetzli_mock_server --port 8080

# Or with debug mode
python -m spaetzli_mock_server --port 8080 --debug
```

### Configure Rotki to use the mock server

You'll need to modify Rotki to point to the mock server. The easiest way is to patch the URLs in `rotkehlchen/premium/premium.py`:

```python
# In Premium.__init__(), change:
self.rotki_api = f'https://rotki.com/api/{self.apiversion}/'
self.rotki_nest = f'https://rotki.com/nest/{self.apiversion}/'

# To:
self.rotki_api = f'http://localhost:8080/api/{self.apiversion}/'
self.rotki_nest = f'http://localhost:8080/nest/{self.apiversion}/'
```

### Enter any API credentials

In Rotki, go to Settings > Premium and enter any API key/secret pair. The mock server accepts any credentials.

Example credentials:
- API Key: `test-key-12345`
- API Secret: `dGVzdC1zZWNyZXQtMTIzNDU=` (base64 encoded)

## Endpoints

### API (`/api/1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/1/last_data_metadata` | GET | Get backup metadata / verify premium |
| `/api/1/statistics_rendererv2` | GET | Get premium Vue components |
| `/api/1/watchers` | GET/PUT/PATCH/DELETE | Manage watchers |
| `/api/1/usage_analytics` | POST | Accept telemetry (ignored) |

### Nest (`/nest/1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/nest/1/limits` | GET | Get user limits & capabilities |
| `/nest/1/devices` | GET | List registered devices |
| `/nest/1/devices` | PUT | Register new device |
| `/nest/1/devices` | PATCH | Edit device name |
| `/nest/1/devices` | DELETE | Delete device |
| `/nest/1/devices/check` | POST | Check if device exists |
| `/nest/1/backup` | GET | Download backup |
| `/nest/1/backup/range` | POST | Upload backup (chunked) |

## Configuration

Default limits (configured in `config.py`):

```python
limit_of_devices = 10
pnl_events_limit = 1_000_000
max_backup_size_mb = 500
history_events_limit = 1_000_000
reports_lookup_limit = 1000
eth_staked_limit = 32_000  # ~1000 validators

eth_staking_view = True
graphs_view = True
event_analysis_view = True
```

## Premium Components

The `/api/1/statistics_rendererv2` endpoint returns stub Vue components by default. To use real premium components:

1. Obtain the premium JavaScript bundle from a legitimate subscription
2. Save it as `data/premium_components.js`
3. The server will serve the real components instead of stubs

## Data Storage

- Device registrations: In-memory (reset on restart)
- Database backups: Stored in `data/backups/`
- Watchers: In-memory (reset on restart)

## License

For personal/educational use only.
