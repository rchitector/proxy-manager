import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import List, Tuple
from .manager import ProxyManager
from .proxy import Proxy
import time

class ProxyChecker:
    """Асинхронный проверщик прокси."""
    
    def __init__(self, manager: ProxyManager, max_concurrent: int = 100):
        self.manager = manager
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)

    async def check_proxy(self, proxy: Proxy) -> bool:
        """
        Проверяет работоспособность прокси.
        
        Args:
            proxy: Прокси для проверки
            
        Returns:
            bool: True если прокси работает, False если нет
        """
        proxy_url = f"{proxy.protocol}://{proxy.ip}:{proxy.port}"
        
        try:
            # Используем более короткий timeout
            timeout = aiohttp.ClientTimeout(total=10)
            
            # Проверяем прокси на нескольких сайтах
            test_urls = [
                'https://coub.com',  # Основной сайт
                'https://api.coub.com/api/v2/timeline/hot',  # API endpoint
                'https://cloudfront.com',  # CDN
            ]
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start_time = time.time()
                
                for url in test_urls:
                    try:
                        async with session.get(
                            url,
                            proxy=proxy_url,
                            ssl=False
                        ) as response:
                            if response.status != 200:
                                self.logger.debug(f"Proxy {proxy_url} failed with status {response.status} on {url}")
                                return False
                            await response.text()
                    except Exception as e:
                        self.logger.debug(f"Proxy {proxy_url} failed on {url}: {str(e)}")
                        return False
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # Если среднее время ответа больше 5 секунд, считаем прокси медленным
                if response_time / len(test_urls) > 5:
                    self.logger.debug(f"Proxy {proxy_url} is too slow: {response_time:.2f}s")
                    return False
                
                proxy.response_time = response_time
                proxy.status = 'working'
                return True
                
        except Exception as e:
            self.logger.debug(f"Proxy {proxy_url} check failed: {str(e)}")
            return False

    def get_unchecked_proxies(self) -> List[Proxy]:
        """
        Получает список непроверенных прокси из базы.
        
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
                LIMIT 100
            """)
            return [Proxy(ip, port, protocol) for ip, port, protocol in cursor.fetchall()]

    def get_random_unchecked_proxies(self, limit: int = 10) -> List[Proxy]:
        """
        Получает список случайных непроверенных прокси из базы.
        
        Args:
            limit: Максимальное количество прокси для проверки
            
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
                ORDER BY RANDOM()
                LIMIT ?
            """, (limit,))
            return [Proxy(ip, port, protocol) for ip, port, protocol in cursor.fetchall()]

    def update_proxy_status(self, proxy: Proxy):
        """
        Обновляет статус прокси в базе.
        
        Args:
            proxy: Прокси для обновления
        """
        current_time = datetime.now().isoformat()
        
        with self.manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE proxies 
                SET status = ?, last_check = ?, response_time = ?
                WHERE ip = ? AND port = ?
            """, (proxy.status, current_time, proxy.response_time, proxy.ip, proxy.port))

    async def check_proxy_batch(self, proxies: List[Proxy]):
        """
        Проверяет пачку прокси параллельно.
        
        Args:
            proxies: Список прокси для проверки
        """
        tasks = []
        for proxy in proxies:
            task = asyncio.create_task(self.check_proxy(proxy))
            tasks.append((proxy, task))
        
        for proxy, task in tasks:
            try:
                is_working = await task
                self.update_proxy_status(proxy)
                status = "working" if is_working else "failed"
                self.logger.info(
                    f"Proxy {proxy.ip}:{proxy.port} status: {status}"
                    f"{f', response time: {proxy.response_time:.3f}s' if is_working else ''}"
                )
            except Exception as e:
                self.logger.error(f"Error checking proxy {proxy.ip}:{proxy.port}: {str(e)}")
                self.update_proxy_status(proxy)

    async def check_all_proxies(self):
        """
        Проверяет все непроверенные прокси в базе.
        """
        proxies = self.get_unchecked_proxies()
        total = len(proxies)
        self.logger.info(f"Starting to check {total} proxies...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for proxy in proxies:
                task = asyncio.create_task(self.check_proxy(proxy))
                tasks.append(task)
            
            # Выполняем проверку и показываем прогресс
            completed = 0
            for coro in asyncio.as_completed(tasks):
                await coro
                completed += 1
                if completed % 10 == 0:  # Показываем прогресс каждые 10 прокси
                    self.logger.info(f"Checked {completed}/{total} proxies...")
        
        self.logger.info("Proxy check completed!")

    async def check_random_proxies(self, limit: int = 10) -> List[Proxy]:
        """
        Проверяет указанное количество случайных непроверенных прокси.
        
        Args:
            limit: Количество прокси для проверки
            
        Returns:
            List[Proxy]: Список рабочих прокси
        """
        proxies = self.get_random_unchecked_proxies(limit)
        total = len(proxies)
        if total == 0:
            self.logger.info("No unchecked proxies found")
            return []
            
        self.logger.info(f"Starting to check {total} random proxies...")
        working_proxies = []
        
        for proxy in proxies:
            is_working = await self.check_proxy(proxy)
            self.update_proxy_status(proxy)
            if is_working:
                working_proxies.append(proxy)
        
        self.logger.info(f"Checked {total}/{total} proxies...")
        self.logger.info("Random proxy check completed!")
        return working_proxies
