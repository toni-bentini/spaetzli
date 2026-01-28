#!/usr/bin/env python3
"""
Spaetzli Docker Entrypoint
Starts the mock premium server, then Rotki backend, colibri, and nginx
"""
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from signal import SIGINT, SIGQUIT, SIGTERM, signal
from types import FrameType
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger('spaetzli')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')

DEFAULT_LOG_LEVEL = 'critical'
MOCK_PORT = 18090


def check_api_availability(url: str, name: str, retries: int = 30, wait_seconds: int = 2) -> bool:
    """Check if an API endpoint is available."""
    for attempt in range(retries):
        try:
            request = Request(url)
            with urlopen(request, timeout=5) as response:
                if response.status == 200:
                    logger.info(f'{name} is ready (attempt {attempt + 1})')
                    return True
        except (HTTPError, URLError, Exception) as e:
            logger.debug(f'{name} not ready: {e}')
        
        if attempt < retries - 1:
            time.sleep(wait_seconds)
    
    logger.error(f'{name} failed to start after {retries} attempts')
    return False


def can_delete(file: Path, cutoff: int) -> bool:
    return int(os.stat(file).st_mtime) <= cutoff or file.name.startswith('_MEI')


def cleanup_tmp() -> None:
    logger.info('Cleaning up tmp directory')
    tmp_dir = Path('/tmp/').glob('*')
    cache_cutoff = datetime.now(tz=UTC) - timedelta(hours=6)
    cutoff_epoch = int(cache_cutoff.strftime('%s'))
    to_delete = filter(lambda x: can_delete(x, cutoff_epoch), tmp_dir)

    deleted = 0
    for item in to_delete:
        path = Path(item)
        try:
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(item)
            deleted += 1
        except (PermissionError, OSError):
            continue

    logger.info(f'Cleaned up {deleted} items from /tmp')


def load_config() -> tuple[list[str], str]:
    """Load configuration from environment and config file."""
    loglevel = os.environ.get('LOGLEVEL', DEFAULT_LOG_LEVEL)
    
    config_file = Path('/config/rotki_config.json')
    if config_file.exists():
        try:
            with open(config_file, encoding='utf-8') as f:
                data = json.load(f)
                loglevel = data.get('loglevel', loglevel)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f'Could not read config file: {e}')
    
    args = [
        '--data-dir', '/data',
        '--logfile', '/logs/rotki.log',
        '--loglevel', loglevel,
    ]
    
    if os.environ.get('LOGFROMOTHERMODULES'):
        args.append('--logfromothermodules')
    
    return args, loglevel


# Global process references
mock_server = None
rotki = None
colibri = None
nginx = None


def graceful_exit(received_signal: int, _frame: FrameType | None) -> None:
    """Handle shutdown gracefully."""
    logger.info(f'Received signal {received_signal}. Shutting down...')
    
    for name, proc in [('nginx', nginx), ('colibri', colibri), ('rotki', rotki), ('mock_server', mock_server)]:
        if proc and proc.poll() is None:
            logger.info(f'Terminating {name}')
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    
    sys.exit(0)


def main():
    global mock_server, rotki, colibri, nginx
    
    cleanup_tmp()
    config_args, log_level = load_config()
    
    # Set up signal handlers
    signal(SIGINT, graceful_exit)
    signal(SIGTERM, graceful_exit)
    signal(SIGQUIT, graceful_exit)
    
    # ============ Start Mock Premium Server ============
    logger.info('🐦 Starting Spaetzli mock premium server...')
    
    mock_env = os.environ.copy()
    mock_env['PYTHONPATH'] = '/opt/spaetzli/deps'
    
    mock_server = subprocess.Popen(
        ['python3', '-m', 'spaetzli_mock_server', '--port', str(MOCK_PORT)],
        cwd='/opt/spaetzli',
        env=mock_env,
    )
    
    if not check_api_availability(f'http://127.0.0.1:{MOCK_PORT}/health', 'Mock server', retries=15):
        logger.error('Mock server failed to start')
        sys.exit(1)
    
    logger.info(f'✅ Mock server running on port {MOCK_PORT}')
    
    # ============ Start Rotki Backend ============
    logger.info('Starting Rotki backend...')
    
    rotki_env = os.environ.copy()
    rotki_env['SPAETZLI_MOCK_URL'] = f'http://127.0.0.1:{MOCK_PORT}'
    
    rotki_cmd = [
        '/usr/sbin/rotki',
        '--rest-api-port', '4242',
        '--api-cors', 'http://localhost:*/*,app://localhost/*',
        '--api-host', '0.0.0.0',
    ] + config_args
    
    logger.info(f'Rotki command: {rotki_cmd}')
    rotki = subprocess.Popen([str(arg) for arg in rotki_cmd], env=rotki_env)
    
    if not check_api_availability('http://127.0.0.1:4242/api/1/ping', 'Rotki backend', retries=30, wait_seconds=3):
        logger.error('Rotki backend failed to start')
        sys.exit(1)
    
    logger.info('✅ Rotki backend ready')
    
    # ============ Start Colibri ============
    logger.info('Starting Colibri...')
    
    colibri_cmd = [
        '/usr/sbin/colibri',
        '--data-directory=/data',
        '--logfile-path=/logs/colibri.log',
        '--port=4343',
        f'--log-level={log_level}',
        '--api-cors=http://localhost:*/*,app://localhost/*',
    ]
    
    colibri = subprocess.Popen(colibri_cmd)
    time.sleep(2)
    
    if colibri.poll() is not None:
        logger.error('Colibri failed to start')
        sys.exit(1)
    
    logger.info('✅ Colibri ready')
    
    # ============ Start Nginx ============
    logger.info('Starting Nginx...')
    
    nginx = subprocess.Popen(['nginx', '-g', 'daemon off;'])
    time.sleep(1)
    
    if nginx.poll() is not None:
        logger.error('Nginx failed to start')
        sys.exit(1)
    
    logger.info('✅ Nginx ready')
    
    # ============ Ready! ============
    logger.info('')
    logger.info('=' * 50)
    logger.info('🐦 Spaetzli is ready!')
    logger.info('')
    logger.info('   Open http://localhost in your browser')
    logger.info('   Enter any API key/secret for premium')
    logger.info('=' * 50)
    logger.info('')
    
    # Monitor processes
    while True:
        time.sleep(30)
        
        for name, proc in [('mock_server', mock_server), ('rotki', rotki), ('nginx', nginx), ('colibri', colibri)]:
            if proc.poll() is not None:
                logger.error(f'{name} has terminated unexpectedly')
                graceful_exit(0, None)
        
        logger.debug('All processes running')


if __name__ == '__main__':
    main()
