from abc import ABC, abstractmethod
from typing import Set
import logging
from ..models import Proxy

class BaseSource(ABC):
    """Базовый класс для всех источников прокси."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_proxies(self) -> Set[Proxy]:
        """Получить список прокси из источника."""
        pass

    def extract_proxies_from_text(self, text: str) -> Set[Proxy]:
        """Извлекает прокси из текста в формате IP:PORT."""
        proxies = set()
        for line in text.splitlines():
            line = line.strip()
            if ':' in line:
                try:
                    ip, port = line.split(':')
                    proxy = Proxy(ip=ip.strip(), port=int(port.strip()))
                    if proxy.is_valid_public_ip:
                        proxies.add(proxy)
                except (ValueError, TypeError):
                    continue
        return proxies
