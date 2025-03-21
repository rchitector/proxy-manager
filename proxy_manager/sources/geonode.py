import requests
from typing import Set
from .base import BaseSource
from ..models import Proxy

class GeonodeSource(BaseSource):
    """Источник прокси с geonode.com."""
    
    def get_proxies(self) -> Set[Proxy]:
        proxies = set()
        url = 'https://proxylist.geonode.com/api/proxy-list'
        params = {
            'limit': 500,
            'page': 1,
            'sort_by': 'lastChecked',
            'sort_type': 'desc',
            'protocols': 'http,https'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('data', []):
                try:
                    proxy = Proxy(
                        ip=item['ip'],
                        port=int(item['port']),
                        protocol=item.get('protocols', ['http'])[0],
                        country=item.get('country', ''),
                        anonymity=item.get('anonymityLevel', '')
                    )
                    if proxy.is_valid_public_ip:
                        proxies.add(proxy)
                except (ValueError, TypeError, KeyError):
                    continue
            
            self.logger.info(f"Found {len(proxies)} proxies from geonode.com")
            
        except Exception as e:
            self.logger.error(f"Error fetching from geonode.com: {str(e)}")
        
        return proxies
