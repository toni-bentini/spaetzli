# Spaetzli 🐦

<p align="center">
  <img src="spaetzli-mascot.png" alt="Spätzli - The Premium Sparrow" width="250">
</p>

<p align="center">
  <em>Unlock Rotki premium features locally</em>
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

## Quick Start

### 1. Clone this repository
```bash
git clone https://github.com/toni-bentini/spaetzli.git
cd spaetzli
```

### 2. Run setup (downloads Rotki & installs dependencies)
```bash
./scripts/setup.sh
```

### 3. Start everything
```bash
./scripts/start.sh
```

### 4. Open Rotki
- Navigate to http://localhost:4242
- Go to **Settings → Premium**
- Enter any API key and secret (e.g., `test` / `dGVzdA==`)
- Enjoy premium features! 🎉

## Manual Setup

If you prefer more control:

```bash
# Terminal 1: Start the mock server
python3 -m spaetzli_mock_server --port 8080

# Terminal 2: Start Rotki with mock
cd rotki
SPAETZLI_MOCK_URL=http://localhost:8080 python3 -m rotkehlchen

# Open http://localhost:4242
```

## Project Structure

```
spaetzli/
├── scripts/
│   ├── setup.sh          # One-time setup
│   └── start.sh          # Start both services
├── spaetzli_mock_server/  # The mock premium server
├── rotki/                 # Rotki source (after setup)
└── plan.md               # Technical documentation
```

## Documentation

- [`spaetzli_mock_server/README.md`](spaetzli_mock_server/README.md) - Mock server API docs
- [`plan.md`](plan.md) - Full technical analysis of Rotki's premium system

## Disclaimer

This project is for **educational and personal use only**. If you find Rotki useful, consider supporting the project with a [premium subscription](https://rotki.com/products).

---

<p align="center">
  Made with 🧡 in Switzerland
</p>
