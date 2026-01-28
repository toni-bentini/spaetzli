"""Configuration for the mock premium server."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PremiumLimits:
    """Premium tier limits configuration."""
    limit_of_devices: int = 10
    pnl_events_limit: int = 1_000_000
    max_backup_size_mb: int = 500
    history_events_limit: int = 1_000_000
    reports_lookup_limit: int = 1000
    eth_staked_limit: int = 32_000  # ~1000 validators


@dataclass
class PremiumCapabilities:
    """Premium tier capabilities."""
    eth_staking_view: bool = True
    graphs_view: bool = True
    event_analysis_view: bool = True


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    
    # Storage paths
    data_dir: Path = field(default_factory=lambda: Path("./data"))
    backups_dir: Path = field(default_factory=lambda: Path("./data/backups"))
    
    # Authentication
    validate_signatures: bool = False  # Set True for strict mode
    
    # Premium configuration
    limits: PremiumLimits = field(default_factory=PremiumLimits)
    capabilities: PremiumCapabilities = field(default_factory=PremiumCapabilities)
    
    def __post_init__(self):
        """Ensure directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)


# Global config instance
config = ServerConfig()
