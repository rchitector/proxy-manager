"""Тесты для ProxyManager."""

import pytest
from datetime import datetime, timedelta
from proxy_manager import ProxyManager
from proxy_manager.proxy import Proxy


def test_add_proxy(proxy_manager, sample_proxies):
    """Тест добавления прокси в базу."""
    proxy_data = sample_proxies[0]
    proxy = Proxy(**proxy_data)
    
    # Добавляем прокси
    proxy_manager.add_proxy(proxy)
    
    # Проверяем, что прокси добавлен
    with proxy_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT ip, port, protocol FROM proxies WHERE ip = ?", (proxy.ip,))
        result = cursor.fetchone()
    
    assert result is not None
    assert result[0] == proxy.ip
    assert result[1] == proxy.port
    assert result[2] == proxy.protocol


def test_get_proxy_by_id(proxy_manager, sample_proxies):
    """Тест получения прокси по ID."""
    proxy_data = sample_proxies[0]
    proxy = Proxy(**proxy_data)
    
    # Добавляем прокси и получаем его ID
    proxy_id = proxy_manager.add_proxy(proxy)
    
    # Получаем прокси по ID
    result = proxy_manager.get_proxy_by_id(proxy_id)
    
    assert result is not None
    assert result.ip == proxy.ip
    assert result.port == proxy.port
    assert result.protocol == proxy.protocol


def test_get_working_proxies(proxy_manager, sample_proxies):
    """Тест получения рабочих прокси."""
    # Добавляем несколько прокси с разными статусами
    proxies = [Proxy(**data) for data in sample_proxies]
    
    # Первый прокси - рабочий
    proxies[0].status = "working"
    proxies[0].response_time = 0.5
    proxy_manager.add_proxy(proxies[0])
    proxy_manager.update_proxy_status(proxies[0])
    
    # Второй прокси - нерабочий
    proxies[1].status = "failed"
    proxy_manager.add_proxy(proxies[1])
    proxy_manager.update_proxy_status(proxies[1])
    
    # Третий прокси - непроверенный
    proxy_manager.add_proxy(proxies[2])
    
    # Получаем рабочие прокси
    working = proxy_manager.get_working_proxies()
    
    assert len(working) == 1
    assert working[0].ip == proxies[0].ip
    assert working[0].status == "working"


def test_mark_proxy_as_failed(proxy_manager, sample_proxies):
    """Тест отметки прокси как нерабочего."""
    proxy_data = sample_proxies[0]
    proxy = Proxy(**proxy_data)
    proxy.status = "working"
    proxy.response_time = 0.5
    
    # Добавляем рабочий прокси
    proxy_id = proxy_manager.add_proxy(proxy)
    
    # Отмечаем как нерабочий
    proxy_manager.mark_proxy_as_failed(proxy_id)
    
    # Проверяем статус
    result = proxy_manager.get_proxy_by_id(proxy_id)
    assert result.status == "failed"


def test_get_statistics(proxy_manager, sample_proxies):
    """Тест получения статистики."""
    # Добавляем прокси с разными статусами
    proxies = [Proxy(**data) for data in sample_proxies]
    
    # Рабочий прокси
    proxies[0].status = "working"
    proxies[0].response_time = 0.5
    proxy_manager.add_proxy(proxies[0])
    proxy_manager.update_proxy_status(proxies[0])
    
    # Нерабочий прокси
    proxies[1].status = "failed"
    proxy_manager.add_proxy(proxies[1])
    proxy_manager.update_proxy_status(proxies[1])
    
    # Непроверенный прокси
    proxy_manager.add_proxy(proxies[2])
    
    stats = proxy_manager.get_statistics()
    
    assert stats["total"] == 3
    assert stats["working"] == 1
    assert stats["failed"] == 1
    assert stats["unchecked"] == 1
    assert stats["outdated"] == 0
    assert stats["avg_response_time"] == 0.5
