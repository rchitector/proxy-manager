"""Модуль для сбора прокси из различных источников."""

import logging
import aiohttp
from typing import List, Dict, Optional
from .proxy import Proxy
from .manager import ProxyManager


class ProxyCollector:
    """Класс для сбора прокси из различных источников."""
    
    def __init__(self, manager: ProxyManager):
        """
        Инициализирует коллектор прокси.
        
        Args:
            manager: Экземпляр ProxyManager для работы с базой прокси
        """
        self.manager = manager
        self.logger = logging.getLogger(__name__)
        
        # Список источников прокси
        self.sources = [
            {
                "url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
                "protocol": "http"
            },
            {
                "url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
                "protocol": "http"
            },
            {
                "url": "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
                "protocol": "http"
            },
            {
                "url": "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
                "protocol": "http"
            },
            {
                "url": "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
                "protocol": "http"
            },
            {
                "url": "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
                "protocol": "http"
            },
            {
                "url": "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
                "protocol": "http"
            },
            {
                "url": "https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt",
                "protocol": "http"
            },
            {
                "url": "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps",
                "protocol": "http"
            }
        ]

    async def _collect_from_api(self, url: str, protocol: str) -> List[Proxy]:
        """
        Собирает прокси из API.
        
        Args:
            url: URL API
            protocol: Протокол прокси (http/https/socks4/socks5)
            
        Returns:
            List[Proxy]: Список собранных прокси
        """
        proxies = []
        try:
            session = aiohttp.ClientSession()
            try:
                async with session:
                    async with await session.get(url, ssl=False) as response:
                        if response.status == 200:
                            text = await response.text()
                            for line in text.split('\n'):
                                if ':' in line:
                                    ip, port = line.strip().split(':')
                                    proxies.append(Proxy(
                                        ip=ip,
                                        port=port,
                                        protocol=protocol
                                    ))
            finally:
                await session.close()
                        
        except Exception as e:
            self.logger.warning(f"Failed to collect from {url}: {str(e)}")
            
        return proxies

    async def collect_all(self) -> None:
        """Собирает прокси из всех источников."""
        total_collected = 0
        unique_proxies = set()  # для отслеживания уникальных прокси
        
        for source in self.sources:
            proxies = await self._collect_from_api(source["url"], source["protocol"])
            
            # Добавляем только уникальные прокси
            for proxy in proxies:
                proxy_key = f"{proxy.ip}:{proxy.port}"
                if proxy_key not in unique_proxies:
                    unique_proxies.add(proxy_key)
                    self.manager.add_proxy(proxy)
                    total_collected += 1
        
        self.logger.info(f"Total unique proxies collected: {total_collected}")
