from dataclasses import dataclass
from typing import Optional
import ipaddress

@dataclass(frozen=True)
class Proxy:
    """Модель прокси-сервера."""
    ip: str
    port: int
    protocol: str = 'http'
    country: str = ''
    anonymity: str = ''
    response_time: float = 0.0

    def __str__(self) -> str:
        return f"{self.ip}:{self.port}"

    @property
    def url(self) -> str:
        """Полный URL прокси."""
        return f"{self.protocol}://{self.ip}:{self.port}"

    @property
    def is_valid_protocol(self) -> bool:
        """Проверяет, является ли протокол поддерживаемым."""
        return self.protocol.lower() in ('http', 'https')

    @property
    def is_valid_public_ip(self) -> bool:
        """Проверяет, является ли IP адрес публичным."""
        try:
            ip = ipaddress.ip_address(self.ip)
            return (
                not ip.is_private and
                not ip.is_loopback and
                not ip.is_link_local and
                not ip.is_multicast and
                not ip.is_reserved and
                not ip.is_unspecified
            )
        except ValueError:
            return False
