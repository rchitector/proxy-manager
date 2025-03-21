# Proxy Manager

A Python package for managing proxy servers. It automatically collects proxies from various sources, validates them, and provides working proxies for your applications.

## Features

- Automatic proxy collection from multiple sources
- Proxy validation and health checking
- Local storage with SQLite
- Simple API to get working proxies
- Cross-platform support

## Installation

```bash
pip install proxy-manager
```

## Usage

```python
from proxy_manager import ProxyManager

# Initialize the manager
manager = ProxyManager()

# Get a single working proxy
proxy = manager.get_working_proxy()
if proxy:
    print(f"Using proxy: {proxy['url']}")
    
# Get multiple working proxies
proxies = manager.get_working_proxies(limit=5)
for proxy in proxies:
    print(f"Proxy from {proxy['country']}: {proxy['url']}")

# Get statistics (for debugging)
stats = manager.get_statistics()
print(f"Working proxies: {stats['working']}")
```

## Data Storage

The package uses the standard user data directory for storing its database:
- Linux: `~/.local/share/proxy-manager/`
- macOS: `~/Library/Application Support/proxy-manager/`
- Windows: `C:\Users\<username>\AppData\Local\proxy-manager\`

## License

MIT License
