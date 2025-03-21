import requests
from bs4 import BeautifulSoup
from typing import Set
from .base import BaseSource
from ..models import Proxy

class FreeProxyListSource(BaseSource):
    """Источник прокси с free-proxy-list.net."""
    
    def get_proxies(self) -> Set[Proxy]:
        proxies = set()
        url = 'https://free-proxy-list.net/'
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 7:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        country = cols[2].text.strip()
                        anonymity = cols[4].text.strip()
                        https = cols[6].text.strip() == 'yes'
                        
                        try:
                            proxy = Proxy(
                                ip=ip,
                                port=int(port),
                                protocol='https' if https else 'http',
                                country=country,
                                anonymity=anonymity
                            )
                            if proxy.is_valid_public_ip:
                                proxies.add(proxy)
                        except (ValueError, TypeError):
                            continue
            
            self.logger.info(f"Found {len(proxies)} proxies from free-proxy-list.net")
            
        except Exception as e:
            self.logger.error(f"Error fetching from free-proxy-list.net: {str(e)}")
        
        return proxies
