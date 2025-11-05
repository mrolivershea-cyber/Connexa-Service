"""
IPQualityScore Integration - Fraud Detection
Проверяет IP на fraud score и risk level после успешного PING OK
"""
import aiohttp
import logging
import os

logger = logging.getLogger(__name__)

class IPQualityScoreChecker:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('IPQS_API_KEY', '')
        self.base_url = "https://ipqualityscore.com/api/json/ip"
        
    async def check_ip(self, ip: str) -> dict:
        """
        Проверить IP через IPQualityScore
        Возвращает: fraud_score (0-100), risk_level (low/medium/high/critical)
        """
        if not self.api_key:
            return {'success': False, 'error': 'API key not configured'}
        
        try:
            url = f"{self.base_url}/{self.api_key}/{ip}"
            params = {
                'strictness': 0,  # 0=less strict, 1=moderate, 2=strict
                'allow_public_access_points': 'true',
                'lighter_penalties': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('success'):
                            fraud_score = data.get('fraud_score', 0)
                            
                            # Определить risk level из fraud_score
                            if fraud_score >= 75:
                                risk_level = 'critical'
                            elif fraud_score >= 50:
                                risk_level = 'high'
                            elif fraud_score >= 25:
                                risk_level = 'medium'
                            else:
                                risk_level = 'low'
                            
                            return {
                                'success': True,
                                'fraud_score': fraud_score,
                                'risk_level': risk_level,
                                'is_proxy': data.get('proxy', False),
                                'is_vpn': data.get('vpn', False),
                                'is_tor': data.get('tor', False),
                                'isp': data.get('ISP', ''),
                                'country': data.get('country_code', ''),
                                'city': data.get('city', ''),
                                'region': data.get('region', ''),
                                'zipcode': data.get('zip_code', '')
                            }
                        else:
                            error_msg = data.get('message', 'Unknown error')
                            logger.warning(f"IPQS failed for {ip}: {error_msg}")
                            return {'success': False, 'error': error_msg}
                    else:
                        logger.error(f"IPQS HTTP {response.status} for {ip}")
                        return {'success': False, 'error': f'HTTP {response.status}'}
                        
        except asyncio.TimeoutError:
            logger.error(f"IPQS timeout for {ip}")
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            logger.error(f"IPQS error for {ip}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def enrich_node_after_ping_ok(self, node, db_session):
        """
        Обогатить узел Scamalytics данными после PING OK
        Заполняет только пустые поля
        """
        # Проверить нужна ли проверка
        needs_check = (node.scamalytics_fraud_score is None or 
                      node.scamalytics_risk is None)
        
        if not needs_check:
            logger.debug(f"Node {node.ip} already has Scamalytics data")
            return False
        
        logger.info(f"🔍 Checking IP {node.ip} with IPQualityScore...")
        
        result = await self.check_ip(node.ip)
        
        if result.get('success'):
            # Обновить ТОЛЬКО пустые поля
            if node.scamalytics_fraud_score is None:
                node.scamalytics_fraud_score = result['fraud_score']
            if node.scamalytics_risk is None:
                node.scamalytics_risk = result['risk_level']
            
            # Бонус: обновить provider если пустой
            if not node.provider and result.get('isp'):
                node.provider = result['isp']
            
            logger.info(f"✅ IPQS: {node.ip} → Fraud={result['fraud_score']}, Risk={result['risk_level']}")
            return True
        else:
            logger.warning(f"❌ IPQS failed for {node.ip}: {result.get('error')}")
            return False

# Глобальный экземпляр
ipqs_checker = IPQualityScoreChecker()
