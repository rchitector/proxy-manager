import requests
from typing import Set, List
from .base import BaseSource
from ..models import Proxy

class GithubSource(BaseSource):
    """Источник прокси из GitHub репозиториев."""
    
    def __init__(self):
        super().__init__()
        self.sources = [
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
            'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt',
            'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
            'https://raw.githubusercontent.com/proxy4parsing/proxy-list/main/http.txt',
            'https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt',
            'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
            'https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt',
            'https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/proxylist.txt'
        ]
    
    def get_proxies(self) -> Set[Proxy]:
        """Получает прокси из всех GitHub источников."""
        all_proxies = set()
        
        for url in self.sources:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                proxies = self.extract_proxies_from_text(response.text)
                all_proxies.update(proxies)
                
                self.logger.info(f"Found {len(proxies)} proxies from {url}")
                
            except Exception as e:
                self.logger.error(f"Error fetching {url}: {str(e)}")
        
        return all_proxies
