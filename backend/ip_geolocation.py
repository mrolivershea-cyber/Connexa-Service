"""
IP Geolocation Service - ip-api.com integration
Автоматически заполняет City/State/ZIP/Provider после PING LIGHT
"""
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

# Rate limiting (45 запросов/минуту)
_last_request_time = 0
_min_interval = 1.4  # секунды между запросами

async def get_ip_geolocation(ip: str) -> dict:
    """
    Получить геолокацию через ip-api.com
    Возвращает: city, state, zip, provider, country
    """
    global _last_request_time
    
    # Rate limiting
    now = asyncio.get_event_loop().time()
    time_since_last = now - _last_request_time
    if time_since_last < _min_interval:
        await asyncio.sleep(_min_interval - time_since_last)
    
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,isp"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                _last_request_time = asyncio.get_event_loop().time()
                
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') == 'success':
                        return {
                            'success': True,
                            'country': data.get('country', ''),
                            'state': data.get('regionName', ''),  # regionName = штат
                            'city': data.get('city', ''),
                            'zipcode': data.get('zip', ''),
                            'provider': data.get('isp', '')  # ISP = провайдер
                        }
                    else:
                        logger.warning(f"IP-API failed for {ip}: {data.get('message')}")
                        return {'success': False, 'error': data.get('message')}
                else:
                    logger.error(f"IP-API HTTP {response.status} for {ip}")
                    return {'success': False, 'error': f'HTTP {response.status}'}
                    
    except asyncio.TimeoutError:
        logger.error(f"IP-API timeout for {ip}")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        logger.error(f"IP-API error for {ip}: {e}")
        return {'success': False, 'error': str(e)}

async def enrich_node_with_geolocation(node, db_session):
    """
    Обогатить узел геолокацией если поля пустые
    Вызывается после успешного PING LIGHT
    """
    # Проверить нужна ли геолокация (если поля уже заполнены - пропустить)
    needs_geo = not node.city or not node.state or not node.zipcode or not node.provider
    
    if not needs_geo:
        logger.debug(f"Node {node.ip} already has location data, skipping IP-API")
        return False
    
    logger.info(f"🌍 Getting geolocation for {node.ip} from IP-API...")
    
    geo_data = await get_ip_geolocation(node.ip)
    
    if geo_data.get('success'):
        # Обновить ТОЛЬКО пустые поля
        if not node.country and geo_data.get('country'):
            node.country = geo_data['country']
        if not node.state and geo_data.get('state'):
            node.state = geo_data['state']
        if not node.city and geo_data.get('city'):
            node.city = geo_data['city']
        if not node.zipcode and geo_data.get('zipcode'):
            node.zipcode = geo_data['zipcode']
        if not node.provider and geo_data.get('provider'):
            node.provider = geo_data['provider']
        
        logger.info(f"✅ Geolocation added for {node.ip}: {geo_data['city']}, {geo_data['state']}")
        return True
    else:
        logger.warning(f"❌ Geolocation failed for {node.ip}: {geo_data.get('error')}")
        return False
