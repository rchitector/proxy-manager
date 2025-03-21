"""Модуль для проверки работоспособности прокси."""

import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import List, Optional
from .proxy import Proxy


class ProxyChecker:
    """Класс для проверки работоспособности прокси."""
    
    def __init__(self, manager):
        """
        Инициализирует чекер прокси.
        
        Args:
            manager: Экземпляр ProxyManager для работы с базой прокси
        """
        self.manager = manager
        self.logger = logging.getLogger(__name__)
        self.check_url = "http://api.ipify.org?format=json"
    
    async def check_proxy(self, proxy: Proxy) -> bool:
        """
        Проверяет работоспособность прокси.
        
        Args:
            proxy: Объект Proxy для проверки
            
        Returns:
            bool: True если прокси работает, False если нет
        """
        start_time = datetime.now()
        proxy_url = f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
        
        try:
            session = aiohttp.ClientSession()
            try:
                async with session:
                    async with await session.get(
                        self.check_url,
                        proxy=proxy_url,
                        timeout=10,
                        ssl=False
                    ) as response:
                        if response.status == 200:
                            await response.text()  # Читаем ответ
                            proxy.response_time = (datetime.now() - start_time).total_seconds()
                            proxy.status = "working"
                            self.manager.update_proxy_status(proxy)
                            return True
                        
                        proxy.status = "failed"
                        self.manager.update_proxy_status(proxy)
                        return False
            finally:
                await session.close()
                        
        except Exception as e:
            self.logger.warning(f"Failed to check proxy {proxy_url}: {str(e)}")
            proxy.status = "failed"
            self.manager.update_proxy_status(proxy)
            return False
    
    def get_unchecked_proxies(self, limit: int = 100) -> List[Proxy]:
        """
        Получает список непроверенных прокси.
        
        Args:
            limit: Максимальное количество прокси
            
        Returns:
            List[Proxy]: Список непроверенных прокси
        """
        with self.manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ip, port, protocol
                FROM proxies
                WHERE status IS NULL
                AND is_outdated = 0
                LIMIT ?
            """, (limit,))
            
            proxies = []
            for row in cursor.fetchall():
                proxy = Proxy(ip=row[0], port=row[1], protocol=row[2])
                proxies.append(proxy)
            return proxies
    
    async def check_random_proxies(self, limit: int = 10) -> List[Proxy]:
        """
        Проверяет случайные прокси из базы.
        
        Args:
            limit: Максимальное количество прокси для проверки
            
        Returns:
            List[Proxy]: Список рабочих прокси
        """
        proxies = self.get_unchecked_proxies(limit)
        working_proxies = []
        
        for proxy in proxies:
            if await self.check_proxy(proxy):
                working_proxies.append(proxy)
        
        return working_proxies
