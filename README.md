# Proxy Manager

A Python package for managing proxy servers. It automatically collects proxies from various sources, validates them, and provides working proxies for your applications.

## Features

- Automatic proxy collection from multiple sources
- Asynchronous proxy validation and health checking
- Local storage with SQLite
- Simple async API to get working proxies
- Cross-platform support

## Installation

```bash
pip install proxy-manager
```

## Usage

```python
import asyncio
from proxy_manager import ProxyManager, ProxyCollector, ProxyChecker

async def main():
    # Initialize the manager
    manager = ProxyManager()
    
    # Collect proxies from sources
    collector = ProxyCollector(manager)
    await collector.collect_all()
    
    # Check and get working proxies
    checker = ProxyChecker(manager)
    working_proxies = await checker.check_random_proxies(20)  # Check 20 random proxies
    
    for proxy in working_proxies:
        print(f"Working proxy: {proxy.protocol}://{proxy.ip}:{proxy.port}")
        print(f"Response time: {proxy.response_time:.2f}s")
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"Total proxies: {stats['total']}")
    print(f"Working proxies: {stats['working']}")
    print(f"Failed proxies: {stats['failed']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Components

- **ProxyManager**: Core class for managing proxies and database operations
- **ProxyCollector**: Collects proxies from various sources
- **ProxyChecker**: Validates proxies and checks their health
- **Proxy**: Data class representing a proxy with its properties

## Data Storage

The package uses SQLite database stored in the standard user data directory:
- Linux: `~/.local/share/proxy-manager/`
- macOS: `~/Library/Application Support/proxy-manager/`
- Windows: `C:\Users\<username>\AppData\Local\proxy-manager\`

## License

MIT License
