"""
AbuseIPDB Integration - Проверка на злоупотребления
Бесплатно: 1000 запросов/день
"""
import aiohttp
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

class AbuseIPDBChecker:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ABUSEIPDB_KEY', '')
        self.base_url = "https://api.abuseipdb.com/api/v2/check"
    
    async def check_ip(self, ip: str) -> dict:
        """Проверить IP через AbuseIPDB"""
        if not self.api_key:
            return {'success': False, 'error': 'API key not configured'}
        
        try:
            headers = {
                'Key': self.api_key,
                'Accept': 'application/json'
            }
            params = {
                'ipAddress': ip,
                'maxAgeInDays': 90,
                'verbose': ''
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, headers=headers, params=params, 
                                      timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        abuse_score = data.get('data', {}).get('abuseConfidenceScore', 0)
                        
                        # Конвертировать abuse score в risk level
                        if abuse_score >= 75:
                            risk_level = 'critical'
                        elif abuse_score >= 50:
                            risk_level = 'high'
                        elif abuse_score >= 25:
                            risk_level = 'medium'
                        else:
                            risk_level = 'low'
                        
                        return {
                            'success': True,
                            'fraud_score': abuse_score,
                            'risk_level': risk_level,
                            'is_public': data.get('data', {}).get('isPublic', False),
                            'usage_type': data.get('data', {}).get('usageType', ''),
                            'isp': data.get('data', {}).get('isp', '')
                        }
                    else:
                        return {'success': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            logger.error(f"AbuseIPDB error for {ip}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def enrich_node(self, node, db_session):
        """Обогатить узел данными AbuseIPDB"""
        if node.scamalytics_fraud_score is not None and node.scamalytics_risk is not None:
            return False
        
        result = await self.check_ip(node.ip)
        
        if result.get('success'):
            if node.scamalytics_fraud_score is None:
                node.scamalytics_fraud_score = result['fraud_score']
            if node.scamalytics_risk is None:
                node.scamalytics_risk = result['risk_level']
            if not node.provider and result.get('isp'):
                node.provider = result['isp']
            
            logger.info(f"✅ AbuseIPDB: {node.ip} → Abuse={result['fraud_score']}, Risk={result['risk_level']}")
            return True
        return False

abuseipdb_checker = AbuseIPDBChecker()
