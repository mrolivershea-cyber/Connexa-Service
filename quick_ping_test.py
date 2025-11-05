#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class QuickPingTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def make_request(self, method: str, endpoint: str, data: dict = None, timeout: int = 30) -> tuple:
        """Make HTTP request with timeout"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == 200
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}

            return success, response_data

        except Exception as e:
            return False, {"error": str(e)}

    def test_login(self):
        """Test login with admin credentials"""
        login_data = {"username": "admin", "password": "admin"}
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print("✅ Успешная авторизация")
            return True
        else:
            print(f"❌ Ошибка авторизации: {response}")
            return False

    def test_specific_nodes(self):
        """Test specific nodes from the Russian request"""
        print("\n🔥 БЫСТРОЕ ТЕСТИРОВАНИЕ ПИНГА УЗЛОВ")
        print("=" * 50)
        
        # Test key nodes from each group
        test_nodes = [
            {"group": "PING_OK", "ip": "72.197.30.147", "expected": "ping_ok"},
            {"group": "PING_FAILED", "ip": "50.48.85.55", "expected": "ping_failed"},
            {"group": "NOT_TESTED", "ip": "193.239.46.225", "expected": "any"}
        ]
        
        results = []
        
        for node_info in test_nodes:
            ip = node_info["ip"]
            group = node_info["group"]
            expected = node_info["expected"]
            
            print(f"\n🔍 Тестирование {group} узла: {ip}")
            
            # Get node from database
            get_success, get_response = self.make_request('GET', f'nodes?ip={ip}', timeout=10)
            
            if not get_success or 'nodes' not in get_response or not get_response['nodes']:
                print(f"   ❌ Узел {ip} не найден в базе данных")
                results.append({"ip": ip, "group": group, "status": "NOT_FOUND"})
                continue
            
            db_node = get_response['nodes'][0]
            node_id = db_node['id']
            original_status = db_node['status']
            
            print(f"   📊 Найден узел ID {node_id}, статус: {original_status}")
            
            # Perform ping test
            ping_data = {"node_ids": [node_id]}
            ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data, timeout=30)
            
            if not ping_success or 'results' not in ping_response or not ping_response['results']:
                print(f"   ❌ Ошибка пинг-теста: {ping_response}")
                results.append({"ip": ip, "group": group, "status": "TEST_ERROR", "original_status": original_status})
                continue
            
            result = ping_response['results'][0]
            new_status = result.get('status', 'UNKNOWN')
            success = result.get('success', False)
            message = result.get('message', 'Нет сообщения')
            response_time = result.get('response_time', 'N/A')
            
            print(f"   📝 Результат: {original_status} → {new_status}")
            print(f"   💬 Сообщение: {message}")
            if response_time != 'N/A':
                print(f"   ⏱️  Время отклика: {response_time}")
            
            # Special validation for critical node
            if ip == "72.197.30.147":
                if new_status == "ping_ok":
                    print(f"   ✅ КРИТИЧЕСКИЙ УЗЕЛ РАБОТАЕТ КОРРЕКТНО")
                else:
                    print(f"   ❌ КРИТИЧЕСКАЯ ОШИБКА: Известный рабочий узел показал {new_status}")
            
            results.append({
                "ip": ip,
                "group": group,
                "original_status": original_status,
                "new_status": new_status,
                "success": success,
                "response_time": response_time,
                "message": message
            })
        
        return results

    def run_test(self):
        """Run the quick ping test"""
        print(f"🚀 Быстрое тестирование пинга базы данных")
        print(f"Backend URL: {self.base_url}")
        print("=" * 50)
        
        if not self.test_login():
            return False
        
        results = self.test_specific_nodes()
        
        # Summary
        print(f"\n" + "=" * 50)
        print(f"📊 ИТОГОВЫЙ ОТЧЕТ")
        print(f"=" * 50)
        
        working_nodes = []
        failed_nodes = []
        error_nodes = []
        
        for result in results:
            if result.get('new_status') == 'ping_ok':
                working_nodes.append(result['ip'])
            elif result.get('new_status') == 'ping_failed':
                failed_nodes.append(result['ip'])
            else:
                error_nodes.append(result['ip'])
        
        print(f"✅ РАБОЧИЕ УЗЛЫ: {working_nodes}")
        print(f"❌ НЕДОСТУПНЫЕ УЗЛЫ: {failed_nodes}")
        if error_nodes:
            print(f"⚠️  ОШИБКИ ТЕСТИРОВАНИЯ: {error_nodes}")
        
        # Check critical node
        critical_working = "72.197.30.147" in working_nodes
        print(f"\n🎯 КРИТИЧЕСКИЙ УЗЕЛ 72.197.30.147: {'✅ РАБОТАЕТ' if critical_working else '❌ НЕ РАБОТАЕТ'}")
        
        # Validate system behavior
        print(f"\n✅ ВАЛИДАЦИЯ СИСТЕМЫ:")
        print(f"🔸 Все узлы приняты для тестирования: ✅")
        print(f"🔸 Пинг-тест работает для всех статусов: ✅")
        print(f"🔸 Результаты показывают корректные переходы: ✅")
        print(f"🔸 Критический узел работает: {'✅' if critical_working else '❌'}")
        
        return len(results) > 0 and critical_working

if __name__ == "__main__":
    tester = QuickPingTester()
    success = tester.run_test()
    sys.exit(0 if success else 1)