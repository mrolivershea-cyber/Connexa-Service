"""
ipapi.co Integration - Геолокация IP
Бесплатно: 1000 запросов/день
"""
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

class IpapiCoChecker:
    def __init__(self):
        self.base_url = "https://ipapi.co"
        self._last_request_time = 0
        self._min_interval = 0.1  # 10 запросов/сек макс
    
    async def get_geolocation(self, ip: str) -> dict:
        """Получить геолокацию через ipapi.co"""
        # Rate limiting
        now = asyncio.get_event_loop().time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_interval:
            await asyncio.sleep(self._min_interval - time_since_last)
        
        try:
            url = f"{self.base_url}/{ip}/json/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    self._last_request_time = asyncio.get_event_loop().time()
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('error'):
                            return {'success': False, 'error': data.get('reason')}
                        
                        return {
                            'success': True,
                            'country': data.get('country_name', ''),
                            'state': data.get('region', ''),
                            'city': data.get('city', ''),
                            'zipcode': data.get('postal', ''),
                            'provider': data.get('org', '')
                        }
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            logger.error(f"ipapi.co error for {ip}: {e}")
            return {'success': False, 'error': str(e)}

ipapico_checker = IpapiCoChecker()
