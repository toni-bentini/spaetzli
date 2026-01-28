# Spaetzli 🐦

<p align="center">
  <img src="spaetzli-mascot.png" alt="Spätzli - The Premium Sparrow" width="250">
</p>

<p align="center">
  <em>Unlock Rotki premium features locally</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg" alt="License: AGPL v3"></a>
</p>

<p align="center">
  <code>curl -fsSL https://raw.githubusercontent.com/toni-bentini/spaetzli/main/install.sh | bash</code>
</p>

<p align="center">
  <sub><b>Requirements:</b> git, curl · <b>Installs to:</b> ~/spaetzli</sub>
</p>

---

**Spaetzli** is a mock server that emulates the Rotki premium API, allowing you to use premium features without a subscription. Perfect for local development, testing, or exploring what premium has to offer.

## What it does

Rotki is an open-source portfolio tracker that offers premium features like:
- 📊 Advanced graphs and statistics
- 💾 Cloud database backup & sync
- 📱 Multi-device support
- ⚡ Higher processing limits
- 🔔 Price watchers & alerts

Spaetzli intercepts premium API calls and responds as if you have an active subscription, enabling all these features locally.

## Requirements

- **git** and **curl** (usually pre-installed on macOS/Linux)
- **Python 3.11+** (for manual setup)
- **Docker** (for Docker setup)
- **uv** (auto-installed by the installer if missing)

## Quick Start

### Option 1: Docker (Recommended)

Everything bundled - just run:

```bash
# Clone the repo
git clone https://github.com/toni-bentini/spaetzli.git
cd spaetzli

# Build and run
./scripts/docker-build.sh
cd docker && docker-compose up
```

Then open http://localhost:8080

### Option 2: One-Line Installer

```bash
curl -fsSL https://raw.githubusercontent.com/toni-bentini/spaetzli/main/install.sh | bash
```

This installs to `~/spaetzli` and sets everything up. Then:

```bash
cd ~/spaetzli && ./scripts/start.sh
```

Open http://localhost:4242

### Option 3: Manual Setup

```bash
# Clone wherever you want
git clone https://github.com/toni-bentini/spaetzli.git
cd spaetzli
./scripts/setup.sh

# Start everything
./scripts/start.sh
```

Then open http://localhost:4242

### Option 4: Full Manual Control

```bash
# Terminal 1: Start the mock server
python3 -m spaetzli_mock_server --port 8080

# Terminal 2: Start Rotki with mock
cd rotki
SPAETZLI_MOCK_URL=http://localhost:8080 python3 -m rotkehlchen

# Open http://localhost:4242
```

---

## How the Patch Works

### The Problem

Rotki has **hardcoded URLs** pointing to rotki.com for premium features:

```python
# Original Rotki code (rotkehlchen/premium/premium.py)
self.rotki_api = f'https://rotki.com/api/1/'
self.rotki_web = f'https://rotki.com/webapi/1/'
self.rotki_nest = f'https://rotki.com/nest/1/'
```

There's no configuration option or environment variable to change this. Every premium API call goes directly to rotki.com.

### The Solution

Spaetzli applies a small patch (~15 lines) that adds environment variable support:

```python
# Patched version
if mock_url := os.environ.get('SPAETZLI_MOCK_URL'):
    log.info(f'Using Spaetzli mock server at {mock_url}')
    self.rotki_api = f'{mock_url}/api/1/'
    self.rotki_web = f'{mock_url}/webapi/1/'
    self.rotki_nest = f'{mock_url}/nest/1/'
else:
    # Original behavior - use rotki.com
    self.rotki_api = f'https://rotki.com/api/1/'
    self.rotki_web = f'https://rotki.com/webapi/1/'
    self.rotki_nest = f'https://rotki.com/nest/1/'
```

### The Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Rotki App     │───▶│  Mock Server    │───▶│ Premium Features│
│  (patched)      │    │  (localhost)    │    │   Unlocked!     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │
         │ SPAETZLI_MOCK_URL    │ "Yes, you have premium!"
         │ =localhost:18090     │ (infinite limits)
         │                      │
```

1. Rotki starts with `SPAETZLI_MOCK_URL` set
2. When checking premium status, it calls our mock server instead of rotki.com
3. Mock server responds with valid premium credentials
4. Rotki enables all premium features locally

---

## Why Not Just Use /etc/hosts?

A common question: "Can't we just add a hosts file entry to redirect rotki.com?"

```bash
# This seems like it would work...
docker run --add-host rotki.com:172.17.0.1 rotki/rotki
```

**Short answer: No, because HTTPS.**

### The HTTPS Problem

Rotki calls `https://rotki.com/...` — note the **https**. For a hosts redirect to work, you'd need:

1. **Valid TLS certificate for rotki.com** — Impossible. We don't own the domain, so no CA will issue us a cert.

2. **Disable certificate verification** — This requires patching Rotki's code anyway (defeats the purpose).

3. **Custom CA + mitmproxy** — Complex setup: generate fake CA, create certs for rotki.com, install CA in container trust store, run proxy. Way more invasive than our 15-line patch.

### Comparison

| Approach | Complexity | Works with HTTPS | Code Changes |
|----------|------------|------------------|--------------|
| **Spaetzli patch** | Low | ✅ Yes | 15 lines |
| Hosts file | Low | ❌ No | None |
| Hosts + disable TLS | Medium | ✅ Yes | More invasive |
| mitmproxy + fake CA | High | ✅ Yes | Container config |

**The patch is the cleanest solution.** It's minimal, doesn't break TLS, and follows Rotki's existing code patterns.

---

## Docker Build Details

### What the Dockerfile Does

```
1. Build mock server (Python deps)
2. Build Rotki frontend (Node.js)
3. Build Rotki backend (Python + Rust)
4. Apply Spaetzli patch to premium.py
5. Package everything with nginx
```

### Build the Image

```bash
./scripts/docker-build.sh

# Or manually:
docker build -f docker/Dockerfile -t spaetzli:latest .
```

### Run with Docker Compose

```bash
cd docker
docker-compose up
```

The compose file:
```yaml
services:
  spaetzli:
    image: spaetzli:latest
    ports:
      - "8080:80"
    volumes:
      - spaetzli-data:/data
      - spaetzli-logs:/logs
```

### Run Directly

```bash
docker run -p 8080:80 \
  -v spaetzli-data:/data \
  -v spaetzli-logs:/logs \
  spaetzli:latest
```

### What's Inside the Container

When the container starts, the entrypoint:

1. **Starts mock server** on port 18090 (internal)
2. **Starts Rotki backend** with `SPAETZLI_MOCK_URL=http://127.0.0.1:18090`
3. **Starts Colibri** (Rotki's Rust service) on port 4343
4. **Starts nginx** on port 80 (external)

All services are monitored - if any crash, the container exits cleanly.

---

## Using Premium Features

Once Spaetzli is running:

1. Open http://localhost:8080 (Docker) or http://localhost:4242 (manual)
2. Go to **Settings → Premium**
3. Enter any API key and secret (e.g., `test` / `dGVzdA==`)
4. Click activate
5. Enjoy all premium features! 🎉

The mock server accepts any credentials and returns valid premium status with unlimited API limits.

---

## Project Structure

```
spaetzli/
├── docker/
│   ├── Dockerfile           # Multi-stage build
│   ├── docker-compose.yml   # Easy deployment
│   └── entrypoint.py        # Process orchestration
├── scripts/
│   ├── setup.sh             # Download Rotki & deps
│   ├── start.sh             # Start all services
│   ├── apply_patch.py       # The premium.py patch
│   └── docker-build.sh      # Build Docker image
├── spaetzli_mock_server/    # The mock premium API
├── rotki/                   # Rotki source (after setup)
└── plan.md                  # Technical analysis
```

## Documentation

- [`spaetzli_mock_server/README.md`](spaetzli_mock_server/README.md) - Mock server API docs
- [`plan.md`](plan.md) - Full technical analysis of Rotki's premium system

---

## Troubleshooting

### Container won't start
Check logs: `docker logs spaetzli`

### Premium not activating
- Make sure you're using the Spaetzli build, not stock Rotki
- Check that mock server is running: `curl http://localhost:8080/health`

### Build fails
- Ensure Docker has enough memory (4GB+ recommended)
- Check that ports 8080/4242 aren't in use

---

## Disclaimer

This project is for **educational and personal use only**. If you find Rotki useful, consider supporting the project with a [premium subscription](https://rotki.com/products).

---

<p align="center">
  Made with 🧡 in Switzerland
</p>
