"""Модуль для сбора прокси из различных источников."""

import aiohttp
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import asyncio


class ProxyCollector:
    """Сборщик прокси из различных источников."""

    def __init__(self, manager):
        """
        Инициализирует сборщик прокси.
        
        Args:
            manager: Менеджер прокси для сохранения собранных прокси
        """
        self.manager = manager
        self.logger = logging.getLogger(__name__)
        self.sources = [
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
            'https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt',
            'https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt',
            'https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt',
            'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt'
        ]
        self.api_sources = [
            'https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps',
            'https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all'
        ]

    async def collect_from_url(self, url: str) -> List[Dict[str, str]]:
        """
        Собирает прокси из указанного URL.
        
        Args:
            url: URL для сбора прокси
            
        Returns:
            List[Dict[str, str]]: Список словарей с данными прокси
        """
        proxies = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        text = await response.text()
                        
                        # Проверяем, является ли это API ответом
                        if url in self.api_sources:
                            if 'geonode' in url:
                                # Парсим ответ GeoNode API
                                import json
                                data = json.loads(text)
                                for item in data.get('data', []):
                                    proxies.append({
                                        'ip': item['ip'],
                                        'port': item['port'],
                                        'protocol': item['protocols'][0]
                                    })
                            else:
                                # Обычный список прокси
                                for line in text.splitlines():
                                    if ':' in line:
                                        ip, port = line.strip().split(':')
                                        proxies.append({
                                            'ip': ip,
                                            'port': port,
                                            'protocol': 'http'
                                        })
                        else:
                            # Обычный текстовый список
                            for line in text.splitlines():
                                if ':' in line:
                                    ip, port = line.strip().split(':')
                                    proxies.append({
                                        'ip': ip,
                                        'port': port,
                                        'protocol': 'http'
                                    })
                        
                        self.logger.info(f"Collected {len(proxies)} proxies from {url}")
                    else:
                        self.logger.warning(f"Failed to collect from {url}: HTTP {response.status}")
        except Exception as e:
            self.logger.error(f"Error collecting from {url}: {str(e)}")
        
        return proxies

    async def collect_all(self) -> None:
        """
        Собирает прокси из всех источников.
        """
        tasks = []
        for url in self.sources + self.api_sources:
            tasks.append(self.collect_from_url(url))
        
        results = await asyncio.gather(*tasks)
        
        # Объединяем все результаты
        all_proxies = []
        for proxies in results:
            all_proxies.extend(proxies)
        
        # Удаляем дубликаты
        unique_proxies = []
        seen = set()
        for proxy in all_proxies:
            key = f"{proxy['ip']}:{proxy['port']}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        # Сохраняем в базу
        current_time = datetime.now().isoformat()
        for proxy in unique_proxies:
            self.manager.add_proxy(
                proxy['ip'],
                int(proxy['port']),
                protocol=proxy['protocol'],
                collection_date=current_time
            )
        
        self.logger.info(f"Total unique proxies collected: {len(unique_proxies)}")
