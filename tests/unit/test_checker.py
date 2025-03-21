"""Тесты для ProxyChecker."""

import pytest
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock
from proxy_manager import ProxyChecker
from proxy_manager.proxy import Proxy


@pytest.fixture
def proxy_checker(proxy_manager):
    """Создает экземпляр ProxyChecker."""
    return ProxyChecker(proxy_manager)


@pytest.mark.asyncio
async def test_check_proxy_success(proxy_checker, sample_proxies):
    """Тест успешной проверки прокси."""
    proxy = Proxy(**sample_proxies[0])
    
    # Создаем мок для ответа
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = '{}'
    mock_response.__aenter__.return_value = mock_response
    
    # Создаем мок для сессии
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value = mock_response
    mock_session.close = AsyncMock()
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await proxy_checker.check_proxy(proxy)
        
    assert result is True
    assert proxy.status == "working"
    assert proxy.response_time is not None


@pytest.mark.asyncio
async def test_check_proxy_failure(proxy_checker, sample_proxies):
    """Тест проверки нерабочего прокси."""
    proxy = Proxy(**sample_proxies[0])
    
    # Мокаем aiohttp.ClientSession с ошибкой
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.side_effect = aiohttp.ClientError()
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await proxy_checker.check_proxy(proxy)
        
    assert result is False


@pytest.mark.asyncio
async def test_check_random_proxies(proxy_checker, sample_proxies, proxy_manager):
    """Тест проверки случайных прокси."""
    # Добавляем тестовые прокси в базу
    for data in sample_proxies:
        proxy = Proxy(**data)
        proxy_manager.add_proxy(proxy)
    
    # Мокаем check_proxy, чтобы первый прокси был рабочим, остальные нет
    async def mock_check_proxy(proxy):
        if proxy.ip == sample_proxies[0]["ip"]:
            proxy.status = "working"
            proxy.response_time = 0.5
            return True
        return False
    
    with patch.object(proxy_checker, 'check_proxy', side_effect=mock_check_proxy):
        working = await proxy_checker.check_random_proxies(limit=3)
    
    assert len(working) == 1
    assert working[0].ip == sample_proxies[0]["ip"]
    assert working[0].status == "working"
    assert working[0].response_time == 0.5


def test_get_unchecked_proxies(proxy_checker, sample_proxies, proxy_manager):
    """Тест получения непроверенных прокси."""
    # Добавляем прокси с разными статусами
    proxies = []
    for data in sample_proxies:
        proxy = Proxy(**data)
        proxy_manager.add_proxy(proxy)
        proxies.append(proxy)
    
    # Отмечаем первый прокси как рабочий
    proxies[0].status = "working"
    proxy_manager.update_proxy_status(proxies[0])
    
    # Получаем непроверенные прокси
    unchecked = proxy_checker.get_unchecked_proxies()
    
    assert len(unchecked) == 2  # два прокси должны остаться непроверенными
    for proxy in unchecked:
        assert proxy.status is None
