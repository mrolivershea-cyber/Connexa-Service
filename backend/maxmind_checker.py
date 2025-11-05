"""
MaxMind GeoIP2 Integration - Геолокация через Web Service
Требует account_id и license_key
"""
import logging
import os

logger = logging.getLogger(__name__)

class MaxMindChecker:
    def __init__(self, account_id: str = None, license_key: str = None):
        self.account_id = account_id or os.getenv('MAXMIND_ACCOUNT_ID', '')
        self.license_key = license_key or os.getenv('MAXMIND_KEY', '')
        self.client = None
        
        # Инициализировать клиент если есть ключи
        if self.account_id and self.license_key:
            try:
                import geoip2.webservice
                self.client = geoip2.webservice.Client(
                    int(self.account_id), 
                    self.license_key
                )
            except ImportError:
                logger.warning("geoip2 library not installed. Install: pip install geoip2")
            except Exception as e:
                logger.error(f"MaxMind client init error: {e}")
    
    async def get_geolocation(self, ip: str) -> dict:
        """Получить геолокацию через MaxMind GeoIP2"""
        if not self.client:
            return {'success': False, 'error': 'MaxMind not configured or geoip2 not installed'}
        
        try:
            # Синхронный вызов в async контексте
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.client.city, ip)
            
            return {
                'success': True,
                'country': response.country.name or '',
                'state': response.subdivisions.most_specific.name or '',
                'city': response.city.name or '',
                'zipcode': response.postal.code or '',
                'provider': ''  # ISP требует отдельный запрос client.isp()
            }
        except Exception as e:
            logger.error(f"MaxMind error for {ip}: {e}")
            return {'success': False, 'error': str(e)}

maxmind_checker = MaxMindChecker()
