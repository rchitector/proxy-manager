#!/usr/bin/env python3
"""Тестовый скрипт для проверки работы пакета proxy_manager."""

import asyncio
import logging
from proxy_manager import ProxyCollector, ProxyChecker, ProxyManager


async def main():
    """Основная функция для тестирования пакета."""
    logging.basicConfig(level=logging.INFO)
    
    # Инициализируем менеджер
    manager = ProxyManager()
    
    print("\n=== Collecting proxies ===")
    collector = ProxyCollector(manager)
    await collector.collect_all()
    
    print("\n=== Checking random proxies ===")
    checker = ProxyChecker(manager)
    working = await checker.check_random_proxies(20)  # Проверяем 20 прокси
    print(f"Found {len(working)} working proxies:")
    for proxy in working:
        print(f"- {proxy.protocol}://{proxy.ip}:{proxy.port} (response time: {proxy.response_time:.2f}s)")
    
    print("\n=== Getting statistics ===")
    stats = manager.get_statistics()
    print("Database statistics:")
    for key, value in stats.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
