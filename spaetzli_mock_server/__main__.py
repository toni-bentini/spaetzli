"""Entry point for the mock premium server."""

import argparse
import uvicorn

from .config import config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="spaetzli-mock-server",
        description="Mock premium server for Rotki",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--validate-signatures",
        action="store_true",
        help="Enable strict signature validation",
    )
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="Directory for storing data (default: ./data)",
    )
    
    args = parser.parse_args()
    
    # Update config
    config.host = args.host
    config.port = args.port
    config.debug = args.debug
    config.validate_signatures = args.validate_signatures
    
    if args.data_dir:
        from pathlib import Path
        config.data_dir = Path(args.data_dir)
        config.backups_dir = config.data_dir / "backups"
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.backups_dir.mkdir(parents=True, exist_ok=True)
    
    # Run server
    uvicorn.run(
        "spaetzli_mock_server.app:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="debug" if config.debug else "info",
    )


if __name__ == "__main__":
    main()
