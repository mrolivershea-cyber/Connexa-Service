"""
Service Manager - Управление всеми чекерами
Выбирает активный сервис на основе настроек
"""
import os
import logging

logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.active_geo_service = 'ip-api'  # По умолчанию
        self.active_fraud_service = 'ipqs'  # По умолчанию
    
    async def get_geolocation(self, ip: str) -> dict:
        """Получить геолокацию через активный сервис"""
        service = os.getenv('GEO_SERVICE', self.active_geo_service)
        
        try:
            if service == 'ip-api':
                from ip_geolocation import get_ip_geolocation
                result = await get_ip_geolocation(ip)
            elif service == 'ipapi.co':
                from ipapico_checker import ipapico_checker
                result = await ipapico_checker.get_geolocation(ip)
            elif service == 'ipinfo':
                from ipinfo_checker import ipinfo_checker
                result = await ipinfo_checker.get_geolocation(ip)
            elif service == 'maxmind':
                from maxmind_checker import maxmind_checker
                result = await maxmind_checker.get_geolocation(ip)
            else:
                # Fallback
                from ip_geolocation import get_ip_geolocation
                result = await get_ip_geolocation(ip)
            
            return result
        except Exception as e:
            logger.error(f"Geolocation service error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def check_fraud(self, ip: str) -> dict:
        """Проверить fraud через активный сервис"""
        service = os.getenv('FRAUD_SERVICE', self.active_fraud_service)
        
        try:
            if service == 'ipqs':
                from ipqs_checker import ipqs_checker
                result = await ipqs_checker.check_ip(ip)
            elif service == 'abuseipdb':
                from abuseipdb_checker import abuseipdb_checker
                result = await abuseipdb_checker.check_ip(ip)
            else:
                # Fallback
                from ipqs_checker import ipqs_checker
                result = await ipqs_checker.check_ip(ip)
            
            return result
        except Exception as e:
            logger.error(f"Fraud service error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def enrich_node_complete(self, node, db_session):
        """
        УМНАЯ ЛОГИКА: Обогатить узел ВСЕМИ данными с автодополнением
        1. Основной сервис (ipqs, abuseipdb и т.д.)
        2. Если не хватает данных → бесплатные сервисы (ip-api.com, ipapi.co)
        """
        fraud_service = os.getenv('FRAUD_SERVICE', self.active_fraud_service)
        
        # Шаг 1: Проверка через основной fraud сервис
        logger.info(f"🎯 Checking {node.ip} with {fraud_service}")
        
        try:
            fraud_result = await self.check_fraud(node.ip)
            
            if fraud_result.get('success'):
                # Заполнить fraud данные
                if node.scamalytics_fraud_score is None:
                    node.scamalytics_fraud_score = fraud_result.get('fraud_score', 0)
                if node.scamalytics_risk is None:
                    node.scamalytics_risk = fraud_result.get('risk_level', 'low')
                
                # Заполнить гео данные если есть
                if not node.country and fraud_result.get('country'):
                    from country_normalize import normalize_country
                    node.country = normalize_country(fraud_result['country'])
                if not node.state and fraud_result.get('region'):
                    node.state = fraud_result['region']
                if not node.city and fraud_result.get('city'):
                    node.city = fraud_result['city']
                if not node.zipcode and fraud_result.get('zipcode'):
                    zip_val = fraud_result['zipcode']
                    if zip_val not in ['N/A', 'NA', 'Unknown']:
                        node.zipcode = zip_val
                if not node.provider and fraud_result.get('isp'):
                    node.provider = fraud_result['isp']
                
                logger.info(f"✅ {fraud_service}: fraud={node.scamalytics_fraud_score}, city={node.city}")
        except Exception as e:
            logger.error(f"{fraud_service} error: {e}")
        
        # Шаг 2: Дополнить недостающие ГЕО данные через БЕСПЛАТНЫЕ сервисы
        needs_geo = not node.city or not node.state or not node.zipcode or not node.provider or not node.coordinates
        
        if needs_geo:
            logger.info(f"📍 {node.ip}: Недостающие гео данные, запрос к бесплатным сервисам...")
            
            # Попытка 1: ip-api.com
            try:
                from ip_geolocation import get_ip_geolocation
                geo_result = await get_ip_geolocation(node.ip)
                
                if geo_result.get('success'):
                    if not node.country:
                        from country_normalize import normalize_country
                        node.country = normalize_country(geo_result.get('country', ''))
                    if not node.state:
                        node.state = geo_result.get('state', '')
                    if not node.city:
                        node.city = geo_result.get('city', '')
                    if not node.zipcode:
                        node.zipcode = geo_result.get('zipcode', '')
                    if not node.provider:
                        node.provider = geo_result.get('provider', '')
                    if not node.coordinates:
                        node.coordinates = geo_result.get('coordinates', '')
                    
                    logger.info(f"✅ ip-api.com: city={node.city}, zip={node.zipcode}, coordinates={node.coordinates}")
            except Exception as e:
                logger.debug(f"ip-api.com error: {e}")
            
            # Попытка 2: Если всё ещё не хватает → ipapi.co
            still_needs = not node.city or not node.state or not node.zipcode
            
            if still_needs:
                try:
                    from ipapico_checker import ipapico_checker
                    geo2_result = await ipapico_checker.get_geolocation(node.ip)
                    
                    if geo2_result.get('success'):
                        if not node.city:
                            node.city = geo2_result.get('city', '')
                        if not node.state:
                            node.state = geo2_result.get('state', '')
                        if not node.zipcode:
                            node.zipcode = geo2_result.get('zipcode', '')
                        
                        logger.info(f"✅ ipapi.co: city={node.city}")
                except Exception as e:
                    logger.debug(f"ipapi.co error: {e}")
        
        return True
    
    async def enrich_node_geolocation(self, node, db_session, force=False):
        """Обогатить узел геолокацией
        
        Args:
            node: Node объект
            db_session: Database session
            force: Если True - проверяет ВСЕГДА, даже если данные есть
        """
        # Принудительная проверка или только если данных нет
        needs_geo = force or (not node.city or not node.state or not node.zipcode)
        
        if not needs_geo:
            return False
        
        result = await self.get_geolocation(node.ip)
        
        if result.get('success'):
            # При force=True - ВСЕГДА обновляем, даже если есть
            if force or not node.country:
                node.country = result.get('country', '')
            if force or not node.state:
                node.state = result.get('state', '')
            if force or not node.city:
                node.city = result.get('city', '')
            if force or not node.zipcode:
                node.zipcode = result.get('zipcode', '')
            if force or not node.provider:
                node.provider = result.get('provider', '')
            return True
        return False
    
    async def enrich_node_fraud(self, node, db_session, force=False):
        """Обогатить узел fraud данными
        
        Args:
            node: Node объект
            db_session: Database session
            force: Если True - проверяет ВСЕГДА, даже если данные есть
        """
        # Принудительная проверка или только если данных нет
        needs_fraud = force or (node.scamalytics_fraud_score is None or node.scamalytics_risk is None)
        
        if not needs_fraud:
            return False
        
        result = await self.check_fraud(node.ip)
        
        if result.get('success'):
            # При force=True - ВСЕГДА обновляем
            if force or node.scamalytics_fraud_score is None:
                node.scamalytics_fraud_score = result.get('fraud_score', 0)
            if force or node.scamalytics_risk is None:
                node.scamalytics_risk = result.get('risk_level', 'low')
            return True
        return False

service_manager = ServiceManager()
