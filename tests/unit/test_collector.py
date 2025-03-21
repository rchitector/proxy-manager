"""Тесты для ProxyCollector."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from proxy_manager import ProxyCollector


@pytest.fixture
def proxy_collector(proxy_manager):
    """Создает экземпляр ProxyCollector."""
    return ProxyCollector(proxy_manager)


@pytest.mark.asyncio
async def test_collect_from_api(proxy_collector):
    """Тест сбора прокси из API."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = "1.2.3.4:8080\n5.6.7.8:3128"
    mock_response.__aenter__.return_value = mock_response
    
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value = mock_response
    mock_session.close = AsyncMock()
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        proxies = await proxy_collector._collect_from_api(
            "http://test.com/proxies",
            "http"
        )
    
    assert len(proxies) == 2
    assert proxies[0].ip == "1.2.3.4"
    assert proxies[0].port == "8080"
    assert proxies[0].protocol == "http"
    assert proxies[1].ip == "5.6.7.8"
    assert proxies[1].port == "3128"
    assert proxies[1].protocol == "http"


@pytest.mark.asyncio
async def test_collect_from_api_failure(proxy_collector):
    """Тест обработки ошибок при сборе прокси."""
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.side_effect = Exception("Connection error")
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        proxies = await proxy_collector._collect_from_api(
            "http://test.com/proxies",
            "http"
        )
    
    assert proxies == []


@pytest.mark.asyncio
async def test_collect_all(proxy_collector):
    """Тест сбора прокси из всех источников."""
    # Мокаем метод _collect_from_api для разных источников
    async def mock_collect(url, protocol):
        if "source1" in url:
            return [
                MagicMock(ip="1.1.1.1", port="80", protocol="http"),
                MagicMock(ip="2.2.2.2", port="8080", protocol="http")
            ]
        elif "source2" in url:
            return [
                MagicMock(ip="3.3.3.3", port="3128", protocol="http")
            ]
        return []
    
    with patch.object(proxy_collector, '_collect_from_api', side_effect=mock_collect):
        # Подменяем список источников на тестовые
        proxy_collector.sources = [
            {"url": "http://source1.com/proxies", "protocol": "http"},
            {"url": "http://source2.com/proxies", "protocol": "http"}
        ]
        
        await proxy_collector.collect_all()
    
    # Проверяем, что прокси были добавлены в базу
    stats = proxy_collector.manager.get_statistics()
    assert stats["total"] == 3  # всего должно быть добавлено 3 уникальных прокси


@pytest.mark.asyncio
async def test_collect_all_with_duplicates(proxy_collector):
    """Тест обработки дубликатов при сборе прокси."""
    # Мокаем метод _collect_from_api, чтобы он возвращал дубликаты
    async def mock_collect(url, protocol):
        return [
            MagicMock(ip="1.1.1.1", port="80", protocol="http"),
            MagicMock(ip="1.1.1.1", port="80", protocol="http"),  # дубликат
            MagicMock(ip="2.2.2.2", port="8080", protocol="http")
        ]
    
    with patch.object(proxy_collector, '_collect_from_api', side_effect=mock_collect):
        proxy_collector.sources = [
            {"url": "http://source1.com/proxies", "protocol": "http"}
        ]
        
        await proxy_collector.collect_all()
    
    # Проверяем, что дубликаты были отфильтрованы
    stats = proxy_collector.manager.get_statistics()
    assert stats["total"] == 2  # должно быть только 2 уникальных прокси
