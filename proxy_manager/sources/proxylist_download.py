import requests
from typing import Set
from .base import BaseSource
from ..models import Proxy

class ProxyListDownloadSource(BaseSource):
    """Источник прокси с proxy-list.download."""
    
    def get_proxies(self) -> Set[Proxy]:
        proxies = set()
        base_url = 'https://www.proxy-list.download/api/v1/get'
        protocols = ['http', 'https']
        
        for protocol in protocols:
            url = f"{base_url}?type={protocol}"
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                new_proxies = self.extract_proxies_from_text(response.text)
                # Устанавливаем правильный протокол
                new_proxies = {
                    Proxy(
                        ip=p.ip,
                        port=p.port,
                        protocol=protocol
                    ) for p in new_proxies
                }
                proxies.update(new_proxies)
                
            except Exception as e:
                self.logger.error(f"Error fetching {protocol} proxies: {str(e)}")
        
        self.logger.info(f"Found {len(proxies)} proxies from proxy-list.download")
        return proxies
