#!/usr/bin/env python3
"""
Focused Speedtest CLI Integration Testing
Tests the critical fix that replaced fake random.uniform() data with real Speedtest.net CLI
"""

import requests
import sys
import json
import time
from datetime import datetime

class SpeedtestCLITester:
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
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        if details:
            print(f"   Details: {details}")

    def make_request(self, method: str, endpoint: str, data: dict = None):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=180)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=180)
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
        """Test login"""
        login_data = {"username": "admin", "password": "admin"}
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log_test("Admin Login", True)
            return True
        else:
            self.log_test("Admin Login", False, f"Login failed: {response}")
            return False

    def test_speedtest_cli_manual_speed_test(self):
        """Test 1: Manual Speed Test with Speedtest CLI - Verify REAL data"""
        print(f"\n🔥 TEST 1: SPEEDTEST CLI INTEGRATION - Manual Speed Test")
        
        # Get a test node with ping_ok or speed_ok status (required for speed testing)
        nodes_success, nodes_response = self.make_request('GET', 'nodes', {'status': 'ping_ok', 'limit': 1})
        
        if not nodes_success or not nodes_response.get('nodes'):
            # Try speed_ok nodes
            nodes_success, nodes_response = self.make_request('GET', 'nodes', {'status': 'speed_ok', 'limit': 1})
            
        if not nodes_success or not nodes_response.get('nodes'):
            # Try not_tested nodes
            nodes_success, nodes_response = self.make_request('GET', 'nodes', {'status': 'not_tested', 'limit': 1})
        
        if not nodes_success or not nodes_response.get('nodes'):
            self.log_test("Speedtest CLI Manual Speed Test", False, "No suitable nodes available for speed testing")
            return False
        
        test_node = nodes_response['nodes'][0]
        node_id = test_node['id']
        
        print(f"📊 Testing speed test on node {node_id} (IP: {test_node.get('ip', 'unknown')}, Status: {test_node.get('status', 'unknown')})")
        
        # Call manual speed test endpoint
        test_data = {"node_ids": [node_id]}
        
        start_time = time.time()
        success, response = self.make_request('POST', 'manual/speed-test', test_data)
        end_time = time.time()
        
        test_duration = end_time - start_time
        
        # Handle both response formats: direct list or {'results': [...]}
        results = response if isinstance(response, list) else response.get('results', [])
        
        if success and len(results) > 0:
            result = results[0]
            
            if not result.get('success'):
                self.log_test("Speedtest CLI Manual Speed Test", False, 
                             f"Speed test failed: {result.get('message', 'Unknown error')}")
                return False
            
            speed_result = result.get('speed_result', {})
            
            # CRITICAL CHECKS
            download_mbps = speed_result.get('download_mbps', 0)
            upload_mbps = speed_result.get('upload_mbps', 0)
            ping_ms = speed_result.get('ping_ms', 0)
            jitter_ms = speed_result.get('jitter_ms', 0)
            message = speed_result.get('message', '')
            method = speed_result.get('method', '')
            
            print(f"\n📊 SPEED TEST RESULTS:")
            print(f"   Download: {download_mbps:.2f} Mbps")
            print(f"   Upload: {upload_mbps:.2f} Mbps")
            print(f"   Ping: {ping_ms:.1f} ms")
            print(f"   Jitter: {jitter_ms:.1f} ms")
            print(f"   Method: {method}")
            print(f"   Duration: {test_duration:.1f}s")
            print(f"   Message: {message}")
            
            # Check 1: Values are not 0
            if download_mbps == 0 or upload_mbps == 0:
                self.log_test("Speedtest CLI Manual Speed Test", False, 
                             f"FAKE DATA DETECTED: download={download_mbps}, upload={upload_mbps}")
                return False
            
            # Check 2: Method field indicates real Speedtest CLI
            if method != "speedtest_cli_real":
                self.log_test("Speedtest CLI Manual Speed Test", False, 
                             f"WRONG METHOD: Expected 'speedtest_cli_real', got '{method}'")
                return False
            
            # Check 3: Message contains correct prefix
            if not message.startswith("SPEED OK (Speedtest.net):"):
                self.log_test("Speedtest CLI Manual Speed Test", False, 
                             f"WRONG MESSAGE FORMAT: Expected 'SPEED OK (Speedtest.net):' prefix")
                return False
            
            # Check 4: Values are realistic
            if download_mbps < 10 or upload_mbps < 10:
                self.log_test("Speedtest CLI Manual Speed Test", False, 
                             f"SUSPICIOUS VALUES: download={download_mbps}, upload={upload_mbps}")
                return False
            
            # Check 5: Ping is reasonable
            if ping_ms > 100:
                self.log_test("Speedtest CLI Manual Speed Test", False, 
                             f"HIGH PING: {ping_ms}ms")
                return False
            
            # All checks passed
            self.log_test("Speedtest CLI Manual Speed Test", True, 
                         f"REAL DATA VERIFIED: {download_mbps:.2f} Mbps down, {upload_mbps:.2f} Mbps up, {ping_ms:.1f}ms ping")
            return True
        else:
            self.log_test("Speedtest CLI Manual Speed Test", False, f"Invalid response: {response}")
            return False
    
    def test_speedtest_cli_result_structure(self):
        """Test 2: Verify Result Structure"""
        print(f"\n🔥 TEST 2: SPEEDTEST CLI RESULT STRUCTURE")
        
        # Get a suitable node
        nodes_success, nodes_response = self.make_request('GET', 'nodes', {'status': 'ping_ok', 'limit': 1})
        
        if not nodes_success or not nodes_response.get('nodes'):
            nodes_success, nodes_response = self.make_request('GET', 'nodes', {'status': 'not_tested', 'limit': 1})
        
        if not nodes_success or not nodes_response.get('nodes'):
            self.log_test("Speedtest CLI Result Structure", False, "No nodes available")
            return False
        
        test_node = nodes_response['nodes'][0]
        node_id = test_node['id']
        
        test_data = {"node_ids": [node_id]}
        success, response = self.make_request('POST', 'manual/speed-test', test_data)
        
        # Handle both response formats
        results = response if isinstance(response, list) else response.get('results', [])
        
        if success and len(results) > 0:
            result = results[0]
            speed_result = result.get('speed_result', {})
            
            # Check for all required fields
            required_fields = ['success', 'download_mbps', 'upload_mbps', 'ping_ms', 'jitter_ms', 'message', 'method']
            missing_fields = [field for field in required_fields if field not in speed_result]
            
            if missing_fields:
                self.log_test("Speedtest CLI Result Structure", False, 
                             f"Missing required fields: {missing_fields}")
                return False
            
            # Verify field types
            type_checks = [
                (isinstance(speed_result['success'], bool), "'success' should be bool"),
                (isinstance(speed_result['download_mbps'], (int, float)), "'download_mbps' should be number"),
                (isinstance(speed_result['upload_mbps'], (int, float)), "'upload_mbps' should be number"),
                (isinstance(speed_result['message'], str), "'message' should be string")
            ]
            
            for check, error_msg in type_checks:
                if not check:
                    self.log_test("Speedtest CLI Result Structure", False, error_msg)
                    return False
            
            self.log_test("Speedtest CLI Result Structure", True, 
                         f"All required fields present with correct types")
            return True
        else:
            self.log_test("Speedtest CLI Result Structure", False, f"Invalid response: {response}")
            return False
    
    def test_speedtest_cli_error_handling(self):
        """Test 3: Error Handling"""
        print(f"\n🔥 TEST 3: SPEEDTEST CLI ERROR HANDLING")
        
        # Try to test a non-existent node
        test_data = {"node_ids": [999999]}
        success, response = self.make_request('POST', 'manual/speed-test', test_data)
        
        # Handle both response formats
        results = response if isinstance(response, list) else response.get('results', [])
        
        if success and len(results) > 0:
            result = results[0]
            
            # Should return error for non-existent node
            if result.get('success') == False and 'not found' in result.get('message', '').lower():
                self.log_test("Speedtest CLI Error Handling", True, 
                             f"Error handling working correctly")
                return True
            else:
                self.log_test("Speedtest CLI Error Handling", False, 
                             f"Expected error for non-existent node")
                return False
        else:
            self.log_test("Speedtest CLI Error Handling", False, f"Invalid response: {response}")
            return False

    def run_all_tests(self):
        """Run all Speedtest CLI tests"""
        print("\n" + "="*80)
        print("SPEEDTEST CLI INTEGRATION TESTING")
        print("Testing the critical fix that replaced fake random.uniform() with real Speedtest.net CLI")
        print("="*80 + "\n")
        
        if not self.test_login():
            print("\n❌ Login failed - cannot continue")
            return False
        
        # Run all Speedtest CLI tests
        self.test_speedtest_cli_manual_speed_test()
        self.test_speedtest_cli_result_structure()
        self.test_speedtest_cli_error_handling()
        
        # Print summary
        print("\n" + "="*80)
        print(f"SPEEDTEST CLI TESTING SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print("="*80 + "\n")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = SpeedtestCLITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
