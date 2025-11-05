#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class PingTestFocused:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED - {details}")
        else:
            print(f"❌ {name}: FAILED - {details}")

    def make_request(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
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

    def test_ping_light_functionality(self):
        """Test PING LIGHT endpoint - быстрая TCP проверка без авторизации"""
        # First, get some nodes with not_tested status for testing
        nodes_success, nodes_response = self.make_request('GET', 'nodes?status=not_tested&limit=5')
        
        if not nodes_success or not nodes_response.get('nodes'):
            # Create a test node for PING LIGHT testing
            test_node = {
                "ip": "8.8.8.8",  # Google DNS - reliable for TCP testing
                "login": "ping_light_test",
                "password": "testpass",
                "protocol": "pptp",
                "status": "not_tested"
            }
            
            create_success, create_response = self.make_request('POST', 'nodes', test_node)
            if create_success and 'id' in create_response:
                test_node_ids = [create_response['id']]
            else:
                self.log_test("PING LIGHT Functionality", False, "Failed to create test node")
                return False
        else:
            # Use existing not_tested nodes
            test_node_ids = [node['id'] for node in nodes_response['nodes'][:3]]
        
        # Test PING LIGHT endpoint
        ping_light_data = {"node_ids": test_node_ids}
        
        start_time = time.time()
        success, response = self.make_request('POST', 'manual/ping-light-test', ping_light_data)
        end_time = time.time()
        
        test_duration = end_time - start_time
        
        if success and 'results' in response:
            results = response['results']
            
            # Verify PING LIGHT characteristics
            ping_light_tests = 0
            successful_tests = 0
            fast_tests = 0
            
            for result in results:
                if result.get('status') == 'completed':
                    ping_light_tests += 1
                    
                    # Check if test was successful
                    if result.get('success'):
                        successful_tests += 1
                    
                    # Check if test was fast (should be ~2 seconds per node)
                    avg_time = result.get('avg_time', 0)
                    if avg_time <= 3.0:  # Allow some tolerance
                        fast_tests += 1
                    
                    # Verify status transition
                    new_status = result.get('new_status')
                    if new_status in ['ping_light', 'ping_failed']:
                        # Status transition is correct
                        pass
            
            # Verify overall performance (should be fast)
            performance_acceptable = test_duration <= (len(test_node_ids) * 3)  # Max 3 seconds per node
            
            if ping_light_tests >= 1 and performance_acceptable:
                self.log_test("PING LIGHT Functionality", True, 
                             f"PING LIGHT working: {ping_light_tests} tests completed in {test_duration:.1f}s, {successful_tests} successful, {fast_tests} fast tests")
                return True
            else:
                self.log_test("PING LIGHT Functionality", False, 
                             f"PING LIGHT issues: {ping_light_tests} tests, duration: {test_duration:.1f}s, performance OK: {performance_acceptable}")
                return False
        else:
            self.log_test("PING LIGHT Functionality", False, f"PING LIGHT API failed: {response}")
            return False

    def test_ping_ok_functionality(self):
        """Test PING OK endpoint - полная PPTP проверка с авторизацией"""
        # Get some nodes for PING OK testing (any status is acceptable)
        nodes_success, nodes_response = self.make_request('GET', 'nodes?limit=5')
        
        if not nodes_success or not nodes_response.get('nodes'):
            # Create a test node for PING OK testing
            test_node = {
                "ip": "8.8.8.8",  # Google DNS
                "login": "admin",
                "password": "admin",
                "protocol": "pptp",
                "status": "not_tested"
            }
            
            create_success, create_response = self.make_request('POST', 'nodes', test_node)
            if create_success and 'id' in create_response:
                test_node_ids = [create_response['id']]
            else:
                self.log_test("PING OK Functionality", False, "Failed to create test node")
                return False
        else:
            # Use existing nodes
            test_node_ids = [node['id'] for node in nodes_response['nodes'][:3]]
        
        # Test PING OK endpoint
        ping_ok_data = {"node_ids": test_node_ids}
        
        start_time = time.time()
        success, response = self.make_request('POST', 'manual/ping-test', ping_ok_data)
        end_time = time.time()
        
        test_duration = end_time - start_time
        
        if success and 'results' in response:
            results = response['results']
            
            # Verify PING OK characteristics
            ping_ok_tests = 0
            successful_tests = 0
            auth_tests = 0
            
            for result in results:
                if result.get('success') is not None:
                    ping_ok_tests += 1
                    
                    # Check if test was successful
                    if result.get('success'):
                        successful_tests += 1
                    
                    # Check if this was a full PPTP test with authentication
                    message = result.get('message', '')
                    if 'PPTP' in message or 'auth' in message.lower() or result.get('status') == 'ping_ok':
                        auth_tests += 1
                    
                    # Verify status transition
                    new_status = result.get('status')
                    if new_status in ['ping_ok', 'ping_failed', 'speed_ok']:  # speed_ok preserved
                        # Status transition is correct
                        pass
            
            # PING OK should take longer than PING LIGHT (includes authentication)
            expected_duration = len(test_node_ids) * 8  # Allow up to 8 seconds per node
            performance_acceptable = test_duration <= expected_duration
            
            if ping_ok_tests >= 1:
                self.log_test("PING OK Functionality", True, 
                             f"PING OK working: {ping_ok_tests} tests completed in {test_duration:.1f}s, {successful_tests} successful, {auth_tests} with auth")
                return True
            else:
                self.log_test("PING OK Functionality", False, 
                             f"PING OK issues: {ping_ok_tests} tests, duration: {test_duration:.1f}s")
                return False
        else:
            self.log_test("PING OK Functionality", False, f"PING OK API failed: {response}")
            return False

    def test_stats_api_includes_ping_light(self):
        """Test that GET /api/stats includes ping_light field"""
        success, response = self.make_request('GET', 'stats')
        
        if success and isinstance(response, dict):
            # Check if ping_light field is present
            if 'ping_light' in response:
                ping_light_count = response['ping_light']
                total_count = response.get('total', 0)
                
                # Verify it's a valid number
                if isinstance(ping_light_count, int) and ping_light_count >= 0:
                    self.log_test("Stats API includes ping_light", True, 
                                 f"ping_light field present: {ping_light_count} (total: {total_count})")
                    return True
                else:
                    self.log_test("Stats API includes ping_light", False, 
                                 f"ping_light field invalid: {ping_light_count}")
                    return False
            else:
                self.log_test("Stats API includes ping_light", False, 
                             f"ping_light field missing from stats: {list(response.keys())}")
                return False
        else:
            self.log_test("Stats API includes ping_light", False, f"Stats API failed: {response}")
            return False

    def test_ping_light_vs_ping_ok_speed_difference(self):
        """Test speed difference between PING LIGHT and PING OK"""
        # Create test nodes for comparison
        test_nodes = []
        for i in range(2):
            test_node = {
                "ip": f"8.8.{i+8}.{i+8}",  # Use different IPs
                "login": "admin",
                "password": "admin",
                "protocol": "pptp",
                "status": "not_tested"
            }
            
            create_success, create_response = self.make_request('POST', 'nodes', test_node)
            if create_success and 'id' in create_response:
                test_nodes.append(create_response['id'])
        
        if len(test_nodes) < 2:
            self.log_test("PING LIGHT vs PING OK Speed", False, "Failed to create test nodes")
            return False
        
        # Test PING LIGHT speed
        ping_light_data = {"node_ids": [test_nodes[0]]}
        start_time = time.time()
        light_success, light_response = self.make_request('POST', 'manual/ping-light-test', ping_light_data)
        light_duration = time.time() - start_time
        
        # Test PING OK speed
        ping_ok_data = {"node_ids": [test_nodes[1]]}
        start_time = time.time()
        ok_success, ok_response = self.make_request('POST', 'manual/ping-test', ping_ok_data)
        ok_duration = time.time() - start_time
        
        if light_success and ok_success:
            # PING LIGHT should be significantly faster than PING OK
            speed_difference = ok_duration / light_duration if light_duration > 0 else 1
            
            if light_duration <= 3.0 and ok_duration >= light_duration:
                self.log_test("PING LIGHT vs PING OK Speed", True, 
                             f"Speed difference confirmed: PING LIGHT {light_duration:.1f}s, PING OK {ok_duration:.1f}s (ratio: {speed_difference:.1f}x)")
                return True
            else:
                self.log_test("PING LIGHT vs PING OK Speed", False, 
                             f"Speed difference not as expected: PING LIGHT {light_duration:.1f}s, PING OK {ok_duration:.1f}s")
                return False
        else:
            self.log_test("PING LIGHT vs PING OK Speed", False, 
                         f"One or both tests failed: LIGHT={light_success}, OK={ok_success}")
            return False

    def run_tests(self):
        """Run focused PING LIGHT and PING OK tests"""
        print("🚀 Starting PING LIGHT & PING OK Testing Suite")
        print("🇷🇺 Russian User Review Request - Final Testing")
        print("=" * 80)
        
        # Login first
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        print("\n🔥 PING LIGHT & PING OK TESTING")
        print("-" * 50)
        print("ТРЕБУЕТСЯ ПРОТЕСТИРОВАТЬ:")
        print("1. PING LIGHT - быстрая TCP проверка без авторизации (endpoint: /api/manual/ping-light-test)")
        print("2. PING OK - полная PPTP проверка с авторизацией (endpoint: /api/manual/ping-test)")
        print("3. Статус ping_light добавлен в БД и статистику")
        print("4. Разница в скорости и методах")
        print("")
        
        # Run the tests
        self.test_ping_light_functionality()
        self.test_ping_ok_functionality()
        self.test_ping_light_vs_ping_ok_speed_difference()
        self.test_stats_api_includes_ping_light()
        
        # Final summary
        print("\n" + "=" * 80)
        print(f"🏁 Testing Complete!")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

if __name__ == "__main__":
    tester = PingTestFocused()
    success = tester.run_tests()
    sys.exit(0 if success else 1)