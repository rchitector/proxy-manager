import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, ContextManager
from contextlib import contextmanager

class ProxyManager:
    """
    Менеджер прокси, предоставляющий интерфейс для работы с прокси-серверами.
    Скрывает детали хранения и обновления прокси.
    """
    
    def __init__(self):
        self.setup_logging()
        
        # Путь к базе данных в текущей директории
        self.db_path = "proxies.db"
        self._setup_database()

    def setup_logging(self):
        """Настройка логирования"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    @contextmanager
    def get_connection(self) -> ContextManager[sqlite3.Connection]:
        """
        Контекстный менеджер для работы с базой данных.
        
        Yields:
            sqlite3.Connection: Соединение с базой данных
        """
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _setup_database(self):
        """Инициализация базы данных (внутренний метод)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proxies (
                    ip TEXT,
                    port INTEGER,
                    protocol TEXT,
                    country TEXT,
                    anonymity TEXT,
                    collection_date TEXT,
                    last_check TEXT,
                    response_time REAL,
                    status TEXT,
                    is_outdated INTEGER DEFAULT 0,
                    PRIMARY KEY (ip, port)
                )
            """)
            # Индексы для оптимизации
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON proxies(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_outdated ON proxies(is_outdated)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_protocol ON proxies(protocol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_collection_date ON proxies(collection_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_check ON proxies(last_check)")

    def mark_all_outdated(self):
        """Помечает все прокси как устаревшие."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE proxies SET is_outdated = 1")
            self.logger.info("All proxies marked as outdated")

    def needs_update(self, max_age_hours: int = 24) -> bool:
        """
        Проверяет, нужно ли обновить базу прокси.
        
        Args:
            max_age_hours: Максимальный возраст данных в часах
            
        Returns:
            bool: True если данные устарели или отсутствуют
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            min_date = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
            
            # Проверяем наличие свежих рабочих прокси
            cursor.execute("""
                SELECT COUNT(*) 
                FROM proxies 
                WHERE status = 'working'
                AND is_outdated = 0
                AND collection_date > ?
            """, (min_date,))
            
            count = cursor.fetchone()[0]
            return count < 10  # Обновляем если меньше 10 свежих рабочих прокси

    def get_working_proxy(self, max_age_hours: int = 24) -> Optional[dict]:
        """
        Получить один рабочий прокси не старше указанного возраста.
        
        Args:
            max_age_hours: Максимальный возраст прокси в часах
            
        Returns:
            dict: Информация о прокси или None если нет рабочих прокси
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            min_date = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
            
            cursor.execute("""
                SELECT ip, port, protocol, country, response_time, last_check
                FROM proxies
                WHERE status = 'working'
                AND is_outdated = 0
                AND last_check > ?
                ORDER BY response_time ASC
                LIMIT 1
            """, (min_date,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'ip': row[0],
                    'port': row[1],
                    'protocol': row[2],
                    'country': row[3],
                    'response_time': row[4],
                    'last_check': row[5],
                    'url': f"{row[2]}://{row[0]}:{row[1]}"
                }
            return None

    def get_working_proxies(self, limit: int = 10, max_age_hours: int = 24) -> List[dict]:
        """
        Получить список рабочих прокси не старше указанного возраста.
        
        Args:
            limit: Максимальное количество прокси
            max_age_hours: Максимальный возраст прокси в часах
            
        Returns:
            List[dict]: Список прокси
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            min_date = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
            
            cursor.execute("""
                SELECT ip, port, protocol, country, response_time, last_check
                FROM proxies
                WHERE status = 'working'
                AND is_outdated = 0
                AND last_check > ?
                ORDER BY response_time ASC
                LIMIT ?
            """, (min_date, limit))
            
            return [{
                'ip': row[0],
                'port': row[1],
                'protocol': row[2],
                'country': row[3],
                'response_time': row[4],
                'last_check': row[5],
                'url': f"{row[2]}://{row[0]}:{row[1]}"
            } for row in cursor.fetchall()]

    def get_random_working_proxy(self, max_age_hours: int = 24) -> Optional[dict]:
        """
        Получает случайный рабочий прокси из базы.
        
        Args:
            max_age_hours: Максимальный возраст прокси в часах
            
        Returns:
            Optional[dict]: Словарь с данными прокси или None если нет рабочих прокси
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            min_date = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
            
            cursor.execute("""
                SELECT ip, port, protocol, response_time, collection_date
                FROM proxies 
                WHERE status = 'working'
                AND is_outdated = 0
                AND collection_date > ?
                ORDER BY RANDOM()
                LIMIT 1
            """, (min_date,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            ip, port, protocol, response_time, collection_date = row
            proxy_url = f"{protocol}://{ip}:{port}"
                
            return {
                "url": proxy_url,
                "ip": ip,
                "port": port,
                "protocol": protocol,
                "response_time": response_time,
                "collection_date": collection_date
            }

    def mark_proxy_as_failed(self, proxy_url: str):
        """
        Помечает прокси как нерабочий.
        
        Args:
            proxy_url: URL прокси для маркировки
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Извлекаем IP и порт из URL
            parts = proxy_url.split('://')[-1].split(':')
            ip = parts[0]
            port = parts[1]
            
            cursor.execute("""
                UPDATE proxies 
                SET status = 'failed',
                    last_check = CURRENT_TIMESTAMP
                WHERE ip = ? AND port = ?
            """, (ip, port))
            conn.commit()

    def get_multiple_working_proxies(self, limit: int = 100, max_age_hours: int = 24) -> List[dict]:
        """
        Получает несколько рабочих прокси из базы.
        
        Args:
            limit: Максимальное количество прокси для получения
            max_age_hours: Максимальный возраст прокси в часах
            
        Returns:
            List[dict]: Список словарей с данными прокси
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            min_date = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
            
            cursor.execute("""
                SELECT ip, port, protocol, response_time, collection_date
                FROM proxies 
                WHERE status = 'working'
                AND is_outdated = 0
                AND collection_date > ?
                ORDER BY response_time ASC
                LIMIT ?
            """, (min_date, limit))
            
            proxies = []
            for row in cursor.fetchall():
                ip, port, protocol, response_time, collection_date = row
                proxy_url = f"{protocol}://{ip}:{port}"
                
                proxies.append({
                    "url": proxy_url,
                    "ip": ip,
                    "port": port,
                    "protocol": protocol,
                    "response_time": response_time,
                    "collection_date": collection_date
                })
            
            return proxies

    def cleanup_old_data(self, max_age_days: int = 7):
        """
        Очистить старые данные из базы.
        
        Args:
            max_age_days: Максимальный возраст данных в днях
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            min_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()
            
            # Удаляем старые прокси
            cursor.execute("""
                DELETE FROM proxies 
                WHERE collection_date < ? 
                OR (status = 'failed' AND last_check < ?)
            """, (min_date, min_date))
            
            deleted = cursor.rowcount
            self.logger.info(f"Cleaned up {deleted} old proxy records")

    def get_statistics(self) -> dict:
        """
        Получить статистику по прокси.
        
        Returns:
            dict: Статистика по прокси
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'working' THEN 1 ELSE 0 END) as working,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status IS NULL THEN 1 ELSE 0 END) as unchecked,
                    SUM(CASE WHEN is_outdated = 1 THEN 1 ELSE 0 END) as outdated,
                    AVG(CASE WHEN status = 'working' THEN response_time ELSE NULL END) as avg_response,
                    MIN(collection_date) as oldest_proxy,
                    MAX(last_check) as latest_check
                FROM proxies
            """)
            row = cursor.fetchone()
            
            stats = {
                'total': row[0] or 0,
                'working': row[1] or 0,
                'failed': row[2] or 0,
                'unchecked': row[3] or 0,
                'outdated': row[4] or 0,
                'avg_response_time': round(row[5], 3) if row[5] else None,
                'oldest_proxy': row[6],
                'latest_check': row[7]
            }
            
            self.logger.info(
                f"Statistics:\n"
                f"Total proxies: {stats['total']}\n"
                f"Working: {stats['working']}\n"
                f"Failed: {stats['failed']}\n"
                f"Unchecked: {stats['unchecked']}\n"
                f"Outdated: {stats['outdated']}\n"
                f"Avg response time: {stats['avg_response_time']}s\n"
                f"Oldest proxy: {stats['oldest_proxy']}\n"
                f"Latest check: {stats['latest_check']}"
            )
            
            return stats

    def add_proxy(self, ip: str, port: int, protocol: str = 'http', collection_date: str = None) -> None:
        """
        Добавляет новый прокси в базу данных.
        
        Args:
            ip: IP адрес прокси
            port: Порт прокси
            protocol: Протокол прокси (http/https)
            collection_date: Дата сбора прокси
        """
        if collection_date is None:
            collection_date = datetime.now().isoformat()
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO proxies (
                    ip, port, protocol, collection_date, is_outdated
                )
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(ip, port) DO UPDATE SET
                    protocol = ?,
                    collection_date = ?,
                    is_outdated = 0
                WHERE ip = ? AND port = ?
            """, (
                ip, port, protocol, collection_date,
                protocol, collection_date,
                ip, port
            ))
