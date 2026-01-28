# Spaetzli 🐦

<p align="center">
  <img src="spaetzli-mascot.png" alt="Spätzli - The Premium Sparrow" width="250">
</p>

<p align="center">
  <em>Unlock Rotki premium features locally</em>
</p>

---

**Spaetzli** is a mock server that emulates the Rotki premium API, allowing you to use premium features without a subscription. Perfect for local development, testing, or just exploring what premium has to offer.

## What it does

Rotki is an open-source portfolio tracker that offers premium features like:
- 📊 Advanced graphs and statistics
- 💾 Cloud database backup & sync
- 📱 Multi-device support
- ⚡ Higher processing limits
- 🔔 Price watchers & alerts

Spaetzli intercepts premium API calls and responds as if you have an active subscription, enabling all these features locally.

## Quick Start

```bash
# Install dependencies
pip install -r spaetzli_mock_server/requirements.txt

# Start the mock server
python -m spaetzli_mock_server --port 8080

# In another terminal, run Rotki with the mock
SPAETZLI_MOCK_URL=http://localhost:8080 python -m rotkehlchen
```

Then enter any API key/secret in Rotki's premium settings — Spaetzli accepts everything!

## Documentation

See [`spaetzli_mock_server/README.md`](spaetzli_mock_server/README.md) for detailed API documentation and configuration options.

See [`plan.md`](plan.md) for the full technical analysis of Rotki's premium system.

## Disclaimer

This project is for **educational and personal use only**. If you find Rotki useful, consider supporting the project with a [premium subscription](https://rotki.com/products).

---

<p align="center">
  Made with 🧡 in Switzerland
</p>
