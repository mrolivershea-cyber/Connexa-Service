#!/usr/bin/env python3
"""
КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: PPTP + SOCKS Integration
Тестирование Start Services функционала

Тестовые сценарии:
1. Тест создания PPTP туннеля вручную
2. Тест запуска SOCKS вручную
3. Тест полного flow через API
4. Тест routing через PPTP
"""

import requests
import sys
import json
import time
import subprocess
from typing import Dict, Any

class PPTPSOCKSIntegrationTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.errors_found = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
            self.errors_found.append(f"{name}: {details}")
        
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def make_request(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}

            return success, response_data

        except Exception as e:
            return False, {"error": str(e)}

    def test_login(self):
        """Test login with admin credentials"""
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log_test("Admin Login", True)
            return True
        else:
            self.log_test("Admin Login", False, f"Login failed: {response}")
            return False

    def get_ping_ok_node(self):
        """Get a node with ping_ok status for testing"""
        success, response = self.make_request('GET', 'nodes?status=ping_ok&limit=1')
        
        if success and 'nodes' in response and response['nodes']:
            node = response['nodes'][0]
            print(f"📍 Found ping_ok node: ID={node['id']}, IP={node['ip']}, Login={node['login']}")
            return node
        
        # Try speed_ok if no ping_ok found
        success, response = self.make_request('GET', 'nodes?status=speed_ok&limit=1')
        if success and 'nodes' in response and response['nodes']:
            node = response['nodes'][0]
            print(f"📍 Found speed_ok node: ID={node['id']}, IP={node['ip']}, Login={node['login']}")
            return node
        
        print("❌ No ping_ok or speed_ok nodes found in database")
        return None

    def test_pptp_tunnel_creation_manual(self):
        """
        ТЕСТ 1: Создание PPTP туннеля вручную
        - Найти узел с ping_ok статусом
        - Вызвать pptp_tunnel_manager.create_tunnel()
        - Проверить создался ли ppp интерфейс
        - Проверить сохранился ли в БД ppp_interface
        """
        print("\n" + "="*80)
        print("ТЕСТ 1: СОЗДАНИЕ PPTP ТУННЕЛЯ ВРУЧНУЮ")
        print("="*80)
        
        node = self.get_ping_ok_node()
        if not node:
            self.log_test("PPTP Tunnel Creation - Find Node", False, "No suitable node found")
            return None
        
        self.log_test("PPTP Tunnel Creation - Find Node", True, f"Found node {node['id']} ({node['ip']})")
        
        # Test PPTP tunnel creation through Python import
        try:
            print(f"\n🔧 Attempting to create PPTP tunnel to {node['ip']}...")
            
            # Import the tunnel manager
            import sys
            sys.path.insert(0, '/app/backend')
            from pptp_tunnel_manager import pptp_tunnel_manager
            
            tunnel_info = pptp_tunnel_manager.create_tunnel(
                node_id=node['id'],
                node_ip=node['ip'],
                username=node['login'],
                password=node['password']
            )
            
            if tunnel_info:
                self.log_test("PPTP Tunnel Creation - create_tunnel()", True, 
                             f"Tunnel created: {tunnel_info['interface']} ({tunnel_info['local_ip']} -> {tunnel_info['remote_ip']})")
                
                # Check if ppp interface exists
                result = subprocess.run(f"ifconfig {tunnel_info['interface']}", 
                                      shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_test("PPTP Tunnel Creation - Interface Check", True, 
                                 f"Interface {tunnel_info['interface']} exists")
                else:
                    self.log_test("PPTP Tunnel Creation - Interface Check", False, 
                                 f"Interface {tunnel_info['interface']} not found")
                
                # Check if ppp_interface saved in DB
                success, response = self.make_request('GET', f'nodes/{node["id"]}')
                if success and response.get('ppp_interface'):
                    self.log_test("PPTP Tunnel Creation - DB Save", True, 
                                 f"ppp_interface saved in DB: {response['ppp_interface']}")
                else:
                    self.log_test("PPTP Tunnel Creation - DB Save", False, 
                                 f"ppp_interface not saved in DB")
                
                return tunnel_info
            else:
                self.log_test("PPTP Tunnel Creation - create_tunnel()", False, 
                             "create_tunnel() returned None")
                
                # Check for CAP_NET_ADMIN capability issue
                result = subprocess.run("cat /var/log/supervisor/backend.err.log | grep -i 'CAP_NET_ADMIN' | tail -n 5", 
                                      shell=True, capture_output=True, text=True)
                if "CAP_NET_ADMIN" in result.stdout:
                    self.errors_found.append("CRITICAL: Container missing CAP_NET_ADMIN capability - PPTP tunnels cannot be created")
                    print(f"\n⚠️  CRITICAL ERROR FOUND:")
                    print(f"   Container is missing CAP_NET_ADMIN capability")
                    print(f"   PPTP tunnels require privileged access to /dev/ppp")
                    print(f"   Solution: Run container with --cap-add=NET_ADMIN or --privileged")
                
                return None
                
        except Exception as e:
            self.log_test("PPTP Tunnel Creation - create_tunnel()", False, f"Exception: {str(e)}")
            self.errors_found.append(f"PPTP tunnel creation exception: {str(e)}")
            return None

    def test_socks_start_manual(self, tunnel_info=None):
        """
        ТЕСТ 2: Запуск SOCKS вручную
        - Вызвать start_socks_service() с параметрами
        - Проверить слушает ли порт
        - Проверить подключение curl --socks5
        """
        print("\n" + "="*80)
        print("ТЕСТ 2: ЗАПУСК SOCKS ВРУЧНУЮ")
        print("="*80)
        
        node = self.get_ping_ok_node()
        if not node:
            self.log_test("SOCKS Start Manual - Find Node", False, "No suitable node found")
            return False
        
        try:
            import sys
            sys.path.insert(0, '/app/backend')
            from socks_server import start_socks_service
            
            # Test parameters
            test_port = 9999
            test_username = f"test_socks_{node['id']}"
            test_password = "test_password_123"
            ppp_interface = tunnel_info['interface'] if tunnel_info else None
            
            print(f"\n🔧 Starting SOCKS5 server on port {test_port}...")
            print(f"   Node: {node['ip']}")
            print(f"   Username: {test_username}")
            print(f"   PPP Interface: {ppp_interface}")
            
            success = start_socks_service(
                node_id=node['id'],
                node_ip=node['ip'],
                port=test_port,
                username=test_username,
                password=test_password,
                ppp_interface=ppp_interface,
                masking_config={}
            )
            
            if success:
                self.log_test("SOCKS Start Manual - start_socks_service()", True, 
                             f"SOCKS server started on port {test_port}")
                
                # Check if port is listening
                time.sleep(2)  # Wait for server to start
                result = subprocess.run(f"netstat -tuln | grep {test_port}", 
                                      shell=True, capture_output=True, text=True)
                
                if str(test_port) in result.stdout:
                    self.log_test("SOCKS Start Manual - Port Listening", True, 
                                 f"Port {test_port} is listening")
                else:
                    self.log_test("SOCKS Start Manual - Port Listening", False, 
                                 f"Port {test_port} is NOT listening")
                
                # Test SOCKS connection with curl
                print(f"\n🧪 Testing SOCKS connection with curl...")
                curl_cmd = f"curl --socks5 {test_username}:{test_password}@127.0.0.1:{test_port} http://httpbin.org/ip --connect-timeout 10 --max-time 15"
                result = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True, timeout=20)
                
                if result.returncode == 0 and "origin" in result.stdout:
                    self.log_test("SOCKS Start Manual - Curl Test", True, 
                                 f"SOCKS connection successful: {result.stdout[:100]}")
                else:
                    self.log_test("SOCKS Start Manual - Curl Test", False, 
                                 f"SOCKS connection failed: {result.stderr[:200]}")
                
                return True
            else:
                self.log_test("SOCKS Start Manual - start_socks_service()", False, 
                             "start_socks_service() returned False")
                return False
                
        except Exception as e:
            self.log_test("SOCKS Start Manual - start_socks_service()", False, f"Exception: {str(e)}")
            self.errors_found.append(f"SOCKS start manual exception: {str(e)}")
            return False

    def test_full_api_flow(self):
        """
        ТЕСТ 3: Полный flow через API
        - POST /api/socks/start для 1 узла
        - Проверить логи
        - Найти ВСЕ ошибки
        """
        print("\n" + "="*80)
        print("ТЕСТ 3: ПОЛНЫЙ FLOW ЧЕРЕЗ API")
        print("="*80)
        
        node = self.get_ping_ok_node()
        if not node:
            self.log_test("Full API Flow - Find Node", False, "No suitable node found")
            return False
        
        self.log_test("Full API Flow - Find Node", True, f"Found node {node['id']} ({node['ip']})")
        
        # Test POST /api/socks/start
        print(f"\n🚀 Testing POST /api/socks/start for node {node['id']}...")
        
        request_data = {
            "node_ids": [node['id']],
            "masking_settings": {
                "obfuscation": False,
                "http_imitation": False,
                "timing_randomization": False,
                "tunnel_encryption": False
            },
            "performance_settings": {},
            "security_settings": {}
        }
        
        success, response = self.make_request('POST', 'socks/start', request_data)
        
        if success:
            self.log_test("Full API Flow - POST /api/socks/start", True, 
                         f"API call successful")
            
            # Check response structure
            if 'results' in response and response['results']:
                result = response['results'][0]
                
                if result.get('success'):
                    self.log_test("Full API Flow - SOCKS Start Success", True, 
                                 f"SOCKS started: {result.get('message', '')}")
                    
                    # Check if node status changed to online
                    success_node, node_response = self.make_request('GET', f'nodes/{node["id"]}')
                    if success_node and node_response.get('status') == 'online':
                        self.log_test("Full API Flow - Node Status Update", True, 
                                     f"Node status changed to 'online'")
                    else:
                        self.log_test("Full API Flow - Node Status Update", False, 
                                     f"Node status is '{node_response.get('status')}', expected 'online'")
                    
                    # Check if SOCKS credentials saved
                    if node_response.get('socks_port') and node_response.get('socks_login'):
                        self.log_test("Full API Flow - SOCKS Credentials Saved", True, 
                                     f"Port: {node_response['socks_port']}, Login: {node_response['socks_login']}")
                    else:
                        self.log_test("Full API Flow - SOCKS Credentials Saved", False, 
                                     "SOCKS credentials not saved in database")
                    
                    return True
                else:
                    self.log_test("Full API Flow - SOCKS Start Success", False, 
                                 f"SOCKS start failed: {result.get('message', '')}")
                    self.errors_found.append(f"API SOCKS start failed: {result.get('message', '')}")
            else:
                self.log_test("Full API Flow - Response Structure", False, 
                             f"Invalid response structure: {response}")
                self.errors_found.append(f"Invalid API response structure")
        else:
            self.log_test("Full API Flow - POST /api/socks/start", False, 
                         f"API call failed: {response}")
            self.errors_found.append(f"API call failed: {response}")
            
            # Check backend logs for errors
            print(f"\n📋 Checking backend logs for errors...")
            result = subprocess.run("tail -n 50 /var/log/supervisor/backend.err.log | grep -i 'error\\|exception\\|failed'", 
                                  shell=True, capture_output=True, text=True)
            if result.stdout:
                print(f"\n⚠️  Backend errors found:")
                print(result.stdout)
                self.errors_found.append(f"Backend errors: {result.stdout[:500]}")
        
        return False

    def test_routing_through_pptp(self):
        """
        ТЕСТ 4: Routing через PPTP
        - Если SOCKS запустился
        - Проверить идет ли трафик через ppp интерфейс
        - Тест curl через SOCKS - какой IP показывает
        """
        print("\n" + "="*80)
        print("ТЕСТ 4: ROUTING ЧЕРЕЗ PPTP")
        print("="*80)
        
        # Get online node with SOCKS
        success, response = self.make_request('GET', 'nodes?status=online&limit=1')
        
        if not success or not response.get('nodes'):
            self.log_test("Routing Test - Find Online Node", False, 
                         "No online nodes with SOCKS found")
            return False
        
        node = response['nodes'][0]
        self.log_test("Routing Test - Find Online Node", True, 
                     f"Found online node {node['id']} with SOCKS on port {node.get('socks_port')}")
        
        # Check if ppp interface exists
        if node.get('ppp_interface'):
            result = subprocess.run(f"ifconfig {node['ppp_interface']}", 
                                  shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_test("Routing Test - PPP Interface Exists", True, 
                             f"Interface {node['ppp_interface']} exists")
            else:
                self.log_test("Routing Test - PPP Interface Exists", False, 
                             f"Interface {node['ppp_interface']} not found")
        else:
            self.log_test("Routing Test - PPP Interface Exists", False, 
                         "No ppp_interface saved in database")
        
        # Test SOCKS connection and check IP
        if node.get('socks_port') and node.get('socks_login') and node.get('socks_password'):
            print(f"\n🧪 Testing SOCKS connection to check routing...")
            
            # Get current IP without SOCKS
            result_direct = subprocess.run("curl -s http://httpbin.org/ip --connect-timeout 10", 
                                         shell=True, capture_output=True, text=True, timeout=15)
            
            # Get IP through SOCKS
            socks_url = f"{node['socks_login']}:{node['socks_password']}@{node.get('socks_ip', '127.0.0.1')}:{node['socks_port']}"
            curl_cmd = f"curl --socks5 {socks_url} http://httpbin.org/ip --connect-timeout 10 --max-time 15"
            result_socks = subprocess.run(curl_cmd, shell=True, capture_output=True, text=True, timeout=20)
            
            if result_socks.returncode == 0 and "origin" in result_socks.stdout:
                self.log_test("Routing Test - SOCKS Connection", True, 
                             f"SOCKS connection successful")
                
                # Compare IPs
                try:
                    import json
                    direct_ip = json.loads(result_direct.stdout).get('origin', 'unknown')
                    socks_ip = json.loads(result_socks.stdout).get('origin', 'unknown')
                    
                    print(f"   Direct IP: {direct_ip}")
                    print(f"   SOCKS IP: {socks_ip}")
                    
                    if direct_ip != socks_ip:
                        self.log_test("Routing Test - IP Change Verification", True, 
                                     f"Traffic routed through PPTP: {direct_ip} -> {socks_ip}")
                    else:
                        self.log_test("Routing Test - IP Change Verification", False, 
                                     f"IP did not change - traffic may not be routed through PPTP")
                except:
                    self.log_test("Routing Test - IP Comparison", False, 
                                 "Could not parse IP addresses")
            else:
                self.log_test("Routing Test - SOCKS Connection", False, 
                             f"SOCKS connection failed: {result_socks.stderr[:200]}")
        else:
            self.log_test("Routing Test - SOCKS Credentials", False, 
                         "SOCKS credentials not found in database")
        
        return True

    def check_for_missing_imports(self):
        """Check for missing imports and undefined variables"""
        print("\n" + "="*80)
        print("ПРОВЕРКА ОТСУТСТВУЮЩИХ ИМПОРТОВ И ПЕРЕМЕННЫХ")
        print("="*80)
        
        # Check for socks_routing_manager
        result = subprocess.run("grep -n 'socks_routing_manager' /app/backend/server.py", 
                              shell=True, capture_output=True, text=True)
        
        if "socks_routing_manager" in result.stdout:
            print(f"\n⚠️  CRITICAL ERROR FOUND:")
            print(f"   socks_routing_manager is used but never defined!")
            print(f"   Location: {result.stdout}")
            
            # Check if it's imported
            result_import = subprocess.run("grep -n 'from.*socks_routing_manager\\|import.*socks_routing_manager' /app/backend/server.py", 
                                         shell=True, capture_output=True, text=True)
            
            if not result_import.stdout:
                self.log_test("Code Check - socks_routing_manager Import", False, 
                             "socks_routing_manager is used but never imported or defined")
                self.errors_found.append("CRITICAL: socks_routing_manager is undefined - will cause NameError")
            else:
                self.log_test("Code Check - socks_routing_manager Import", True, 
                             f"socks_routing_manager is imported: {result_import.stdout}")
        
        # Check for other potential issues
        result = subprocess.run("grep -n 'TODO\\|FIXME\\|XXX\\|HACK' /app/backend/server.py | head -n 10", 
                              shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print(f"\n📝 Code comments found:")
            print(result.stdout)

    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*80)
        print("КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: PPTP + SOCKS INTEGRATION")
        print("="*80)
        
        # Login first
        if not self.test_login():
            print("\n❌ Cannot proceed without login")
            return
        
        # Check for code issues first
        self.check_for_missing_imports()
        
        # Test 1: PPTP tunnel creation
        tunnel_info = self.test_pptp_tunnel_creation_manual()
        
        # Test 2: SOCKS start manual
        self.test_socks_start_manual(tunnel_info)
        
        # Test 3: Full API flow
        self.test_full_api_flow()
        
        # Test 4: Routing through PPTP
        self.test_routing_through_pptp()
        
        # Print summary
        print("\n" + "="*80)
        print("ИТОГОВЫЙ ОТЧЕТ")
        print("="*80)
        print(f"Всего тестов: {self.tests_run}")
        print(f"Успешно: {self.tests_passed}")
        print(f"Провалено: {self.tests_run - self.tests_passed}")
        print(f"Процент успеха: {(self.tests_passed/self.tests_run*100) if self.tests_run > 0 else 0:.1f}%")
        
        if self.errors_found:
            print(f"\n🔥 НАЙДЕННЫЕ КРИТИЧЕСКИЕ ОШИБКИ ({len(self.errors_found)}):")
            for i, error in enumerate(self.errors_found, 1):
                print(f"\n{i}. {error}")
        else:
            print(f"\n✅ Критических ошибок не найдено")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    tester = PPTPSOCKSIntegrationTester()
    tester.run_all_tests()
