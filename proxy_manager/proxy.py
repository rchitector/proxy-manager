"""Модуль для работы с прокси."""

class Proxy:
    """Класс для представления прокси."""
    
    def __init__(self, ip: str, port: int, protocol: str = 'http'):
        """
        Инициализирует объект прокси.
        
        Args:
            ip: IP адрес прокси
            port: Порт прокси
            protocol: Протокол прокси (http/https)
        """
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.status = None
        self.response_time = None
        self.collection_date = None
        self.last_check = None
        
    @property
    def url(self) -> str:
        """Возвращает URL прокси."""
        return f"{self.protocol}://{self.ip}:{self.port}"
