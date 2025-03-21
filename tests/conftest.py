"""Общие фикстуры для тестов."""

import os
import pytest
import sqlite3
from proxy_manager import ProxyManager


@pytest.fixture
def temp_db_path(tmp_path):
    """Создает временную базу данных для тестов."""
    db_path = tmp_path / "test.db"
    return str(db_path)


@pytest.fixture
def proxy_manager(temp_db_path, monkeypatch):
    """Создает экземпляр ProxyManager с временной базой данных."""
    manager = ProxyManager()
    monkeypatch.setattr(manager, "db_path", temp_db_path)
    manager._setup_database()
    return manager


@pytest.fixture
def sample_proxies():
    """Возвращает список тестовых прокси."""
    return [
        {"ip": "1.2.3.4", "port": "8080", "protocol": "http"},
        {"ip": "5.6.7.8", "port": "3128", "protocol": "http"},
        {"ip": "9.10.11.12", "port": "80", "protocol": "https"}
    ]