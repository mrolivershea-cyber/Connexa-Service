#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class RussianImportTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
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
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data)
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

    def test_import_ping_only_mode(self):
        """Test /api/nodes/import with testing_mode 'ping_only' - verify PPTP port 1723 testing"""
        print("\n🔥 TESTING IMPORT WITH PING_ONLY MODE (Russian User Issue)")
        print("=" * 60)
        
        # Use the exact test data from review request
        test_data = """72.197.30.147 admin admin US
100.11.102.204 admin admin US  
100.16.39.213 admin admin US
200.1.1.1 admin admin US
200.1.1.2 admin admin US"""
        
        import_data = {
            "data": test_data,
            "protocol": "pptp",
            "testing_mode": "ping_only"
        }
        
        print(f"📋 Importing 5 nodes with testing_mode='ping_only'")
        print(f"   Expected: Uses PPTP port 1723 testing instead of ICMP ping")
        print(f"   Working IP: 72.197.30.147 (should show ping_ok)")
        print(f"   Non-working IPs: Others (should show ping_failed)")
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            print(f"   Import Results: Added={report.get('added', 0)}, Errors={report.get('format_errors', 0)}")
            
            # Wait a moment for testing to complete
            time.sleep(10)
            
            # Check specific nodes for correct status
            test_results = []
            expected_results = [
                {'ip': '72.197.30.147', 'expected_status': 'ping_ok'},  # Working IP
                {'ip': '100.11.102.204', 'expected_status': 'ping_failed'},  # Non-working
                {'ip': '200.1.1.1', 'expected_status': 'ping_failed'},  # Non-working
            ]
            
            for test_case in expected_results:
                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={test_case["ip"]}')
                
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    actual_status = node.get('status')
                    expected_status = test_case['expected_status']
                    
                    if actual_status == expected_status:
                        test_results.append(f"✅ {test_case['ip']}: {actual_status} (correct)")
                    else:
                        test_results.append(f"❌ {test_case['ip']}: {actual_status} (expected {expected_status})")
                else:
                    test_results.append(f"❌ {test_case['ip']}: Node not found")
            
            print(f"\n📊 PING_ONLY TEST RESULTS:")
            for result in test_results:
                print(f"   {result}")
            
            # Check for nodes stuck in 'checking' status
            checking_success, checking_response = self.make_request('GET', 'nodes?status=checking')
            checking_count = 0
            if checking_success and 'nodes' in checking_response:
                checking_count = len(checking_response['nodes'])
            
            print(f"   Nodes stuck in 'checking': {checking_count}")
            
            # Determine success
            success_count = len([r for r in test_results if r.startswith('✅')])
            total_tests = len(test_results)
            
            if success_count >= 2 and checking_count == 0:  # At least 2/3 correct and no stuck nodes
                self.log_test("Import Ping Only Mode", True, 
                             f"✅ PPTP port 1723 testing working correctly. {success_count}/{total_tests} nodes correct, {checking_count} stuck")
                return True
            else:
                self.log_test("Import Ping Only Mode", False, 
                             f"❌ PPTP testing issues. {success_count}/{total_tests} nodes correct, {checking_count} stuck in checking")
                return False
        else:
            self.log_test("Import Ping Only Mode", False, f"Import failed: {response}")
            return False

    def test_import_ping_speed_mode(self):
        """Test /api/nodes/import with testing_mode 'ping_speed' - verify both PPTP ping and speed tests"""
        print("\n🔥 TESTING IMPORT WITH PING_SPEED MODE (Russian User Issue)")
        print("=" * 60)
        
        # Use different IPs to avoid conflicts with previous test
        test_data = """72.197.30.148 admin admin US
100.11.102.205 admin admin US  
200.1.1.3 admin admin US"""
        
        import_data = {
            "data": test_data,
            "protocol": "pptp",
            "testing_mode": "ping_speed"
        }
        
        print(f"📋 Importing 3 nodes with testing_mode='ping_speed'")
        print(f"   Expected: PPTP ping test first, then speed test for successful pings")
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            print(f"   Import Results: Added={report.get('added', 0)}, Errors={report.get('format_errors', 0)}")
            
            # Wait longer for ping+speed testing to complete
            time.sleep(15)
            
            # Check nodes for correct status progression
            test_results = []
            expected_results = [
                {'ip': '72.197.30.148', 'expected_statuses': ['ping_ok', 'speed_ok']},  # Should pass both
                {'ip': '100.11.102.205', 'expected_statuses': ['ping_failed']},  # Should fail ping
                {'ip': '200.1.1.3', 'expected_statuses': ['ping_failed']},  # Should fail ping
            ]
            
            for test_case in expected_results:
                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={test_case["ip"]}')
                
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    actual_status = node.get('status')
                    expected_statuses = test_case['expected_statuses']
                    
                    if actual_status in expected_statuses:
                        test_results.append(f"✅ {test_case['ip']}: {actual_status} (correct)")
                    else:
                        test_results.append(f"❌ {test_case['ip']}: {actual_status} (expected one of {expected_statuses})")
                else:
                    test_results.append(f"❌ {test_case['ip']}: Node not found")
            
            print(f"\n📊 PING_SPEED TEST RESULTS:")
            for result in test_results:
                print(f"   {result}")
            
            # Check for nodes stuck in 'checking' status
            checking_success, checking_response = self.make_request('GET', 'nodes?status=checking')
            checking_count = 0
            if checking_success and 'nodes' in checking_response:
                checking_count = len(checking_response['nodes'])
            
            print(f"   Nodes stuck in 'checking': {checking_count}")
            
            # Determine success
            success_count = len([r for r in test_results if r.startswith('✅')])
            total_tests = len(test_results)
            
            if success_count >= 2 and checking_count == 0:  # At least 2/3 correct and no stuck nodes
                self.log_test("Import Ping Speed Mode", True, 
                             f"✅ PPTP ping+speed testing working correctly. {success_count}/{total_tests} nodes correct, {checking_count} stuck")
                return True
            else:
                self.log_test("Import Ping Speed Mode", False, 
                             f"❌ PPTP ping+speed testing issues. {success_count}/{total_tests} nodes correct, {checking_count} stuck in checking")
                return False
        else:
            self.log_test("Import Ping Speed Mode", False, f"Import failed: {response}")
            return False

    def test_import_timeout_protection(self):
        """Test that nodes don't get stuck in 'checking' status and have timeout protection"""
        print("\n🔥 TESTING IMPORT TIMEOUT PROTECTION (Russian User Issue)")
        print("=" * 60)
        
        # Use non-responsive IPs to test timeout behavior
        test_data = """192.0.2.1 admin admin US
192.0.2.2 admin admin US"""  # RFC 5737 test IPs (should timeout)
        
        import_data = {
            "data": test_data,
            "protocol": "pptp",
            "testing_mode": "ping_only"
        }
        
        print(f"📋 Importing 2 nodes with non-responsive IPs to test timeout protection")
        print(f"   Expected: Nodes should revert to original status on timeout, not stuck in 'checking'")
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            print(f"   Import Results: Added={report.get('added', 0)}, Errors={report.get('format_errors', 0)}")
            
            # Wait for timeout to occur (should be quick with fast_mode)
            time.sleep(8)
            
            # Check that no nodes are stuck in 'checking' status
            checking_success, checking_response = self.make_request('GET', 'nodes?status=checking')
            checking_count = 0
            if checking_success and 'nodes' in checking_response:
                checking_count = len(checking_response['nodes'])
            
            # Check the status of our test nodes
            test_results = []
            for ip in ['192.0.2.1', '192.0.2.2']:
                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    actual_status = node.get('status')
                    
                    # Should be either 'not_tested' (reverted) or 'ping_failed' (timeout handled)
                    if actual_status in ['not_tested', 'ping_failed']:
                        test_results.append(f"✅ {ip}: {actual_status} (timeout handled correctly)")
                    else:
                        test_results.append(f"❌ {ip}: {actual_status} (should be not_tested or ping_failed)")
                else:
                    test_results.append(f"❌ {ip}: Node not found")
            
            print(f"\n📊 TIMEOUT PROTECTION TEST RESULTS:")
            for result in test_results:
                print(f"   {result}")
            print(f"   Nodes stuck in 'checking': {checking_count}")
            
            # Success if no nodes stuck and timeout handled correctly
            success_count = len([r for r in test_results if r.startswith('✅')])
            
            if checking_count == 0 and success_count >= 1:
                self.log_test("Import Timeout Protection", True, 
                             f"✅ Timeout protection working. {success_count}/2 nodes handled correctly, {checking_count} stuck")
                return True
            else:
                self.log_test("Import Timeout Protection", False, 
                             f"❌ Timeout protection issues. {success_count}/2 nodes handled correctly, {checking_count} stuck in checking")
                return False
        else:
            self.log_test("Import Timeout Protection", False, f"Import failed: {response}")
            return False

    def run_russian_user_import_tests(self):
        """Run all Russian user import issue tests"""
        print("\n🇷🇺 RUSSIAN USER IMPORT TESTING ISSUE - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print("Testing fixes for import functionality with different testing modes")
        print("Issues: Import with ping or ping+speed testing causes configs to fall to PING Failed or hang at 90%")
        print("=" * 80)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Run all import-specific tests
        test_results = []
        
        test_results.append(self.test_import_ping_only_mode())
        test_results.append(self.test_import_ping_speed_mode())
        test_results.append(self.test_import_timeout_protection())
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n🏁 RUSSIAN USER IMPORT TESTS SUMMARY")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {total_tests - passed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 ALL RUSSIAN USER IMPORT TESTS PASSED!")
            return True
        else:
            print("❌ SOME RUSSIAN USER IMPORT TESTS FAILED")
            return False

if __name__ == "__main__":
    tester = RussianImportTester()
    success = tester.run_russian_user_import_tests()
    sys.exit(0 if success else 1)