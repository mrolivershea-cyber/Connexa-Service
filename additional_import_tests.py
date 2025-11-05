#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class AdditionalImportTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def make_request(self, method: str, endpoint: str, data=None, expected_status: int = 200):
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
        """Login with admin credentials"""
        login_data = {"username": "admin", "password": "admin"}
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_backend_hardcoded_no_test(self):
        """Test that backend is hardcoded to use no_test mode"""
        print("🔍 TESTING BACKEND HARDCODED NO_TEST MODE")
        print("=" * 60)
        
        # Try to force different testing modes - should all be ignored
        test_cases = [
            {"testing_mode": "ping_only"},
            {"testing_mode": "speed_only"},
            {"testing_mode": "both"},
            {"testing_mode": "invalid_mode"},
            # No testing_mode field
            {}
        ]
        
        for i, test_data in enumerate(test_cases, 1):
            import_data = {
                "data": f"192.168.200.{i} testuser{i} testpass{i} CA",
                "protocol": "pptp"
            }
            import_data.update(test_data)
            
            success, response = self.make_request('POST', 'nodes/import', import_data)
            
            if success and 'report' in response:
                testing_mode = response['report'].get('testing_mode')
                session_id = response.get('session_id')
                
                print(f"   Test {i}: Input={test_data.get('testing_mode', 'None')} → Output='{testing_mode}', session_id={session_id}")
                
                if testing_mode != 'no_test' or session_id is not None:
                    print(f"   ❌ FAILED: Expected testing_mode='no_test' and session_id=None")
                    return False
            else:
                print(f"   ❌ FAILED: Import request failed: {response}")
                return False
        
        print("   ✅ SUCCESS: Backend always forces testing_mode='no_test' regardless of input")
        return True

    def test_no_background_testing_processes(self):
        """Test that no background testing processes are started"""
        print("\n🔍 TESTING NO BACKGROUND TESTING PROCESSES")
        print("=" * 60)
        
        # Import multiple nodes
        import_data = {
            "data": """192.168.201.1 bgtest1 testpass1 CA
192.168.201.2 bgtest2 testpass2 TX
192.168.201.3 bgtest3 testpass3 FL
192.168.201.4 bgtest4 testpass4 NY
192.168.201.5 bgtest5 testpass5 WA""",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if not success:
            print("   ❌ FAILED: Import request failed")
            return False
        
        print("   ✅ Import completed successfully")
        
        # Wait and check multiple times to ensure no background testing
        check_intervals = [5, 10, 15, 20]  # seconds
        
        for interval in check_intervals:
            print(f"   Waiting {interval}s and checking node statuses...")
            time.sleep(5 if interval == 5 else 5)  # Wait 5s each time
            
            all_still_not_tested = True
            for i in range(1, 6):
                ip = f"192.168.201.{i}"
                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    status = node.get('status')
                    
                    if status != 'not_tested':
                        print(f"   ❌ FAILED: Node {ip} status changed to '{status}' (background testing detected!)")
                        all_still_not_tested = False
                        break
                else:
                    print(f"   ❌ FAILED: Node {ip} not found")
                    all_still_not_tested = False
                    break
            
            if not all_still_not_tested:
                return False
            
            print(f"   ✅ After {interval}s: All nodes still 'not_tested'")
        
        print("   ✅ SUCCESS: No background testing processes detected after 20 seconds")
        return True

    def test_progress_endpoint_not_created(self):
        """Test that no progress tracking sessions are created"""
        print("\n🔍 TESTING NO PROGRESS SESSIONS CREATED")
        print("=" * 60)
        
        # Import nodes
        import_data = {
            "data": "192.168.202.1 progresstest testpass CA",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if not success:
            print("   ❌ FAILED: Import request failed")
            return False
        
        session_id = response.get('session_id')
        
        if session_id is not None:
            print(f"   ❌ FAILED: session_id returned: {session_id}")
            return False
        
        print("   ✅ SUCCESS: No session_id returned, no progress sessions created")
        return True

    def test_import_with_large_dataset(self):
        """Test simplified import with larger dataset"""
        print("\n🔍 TESTING LARGE DATASET IMPORT")
        print("=" * 60)
        
        # Create 50 test nodes
        nodes_data = []
        for i in range(1, 51):
            nodes_data.append(f"192.168.203.{i} largetest{i} testpass{i} CA")
        
        import_data = {
            "data": "\n".join(nodes_data),
            "protocol": "pptp"
        }
        
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        end_time = time.time()
        
        if not success:
            print("   ❌ FAILED: Large import request failed")
            return False
        
        duration = end_time - start_time
        report = response.get('report', {})
        added = report.get('added', 0)
        testing_mode = report.get('testing_mode')
        session_id = response.get('session_id')
        
        print(f"   Import duration: {duration:.2f} seconds")
        print(f"   Nodes added: {added}")
        print(f"   Testing mode: {testing_mode}")
        print(f"   Session ID: {session_id}")
        
        if testing_mode == 'no_test' and session_id is None and added >= 45:  # Allow for some duplicates
            print("   ✅ SUCCESS: Large dataset imported correctly in simplified mode")
            return True
        else:
            print("   ❌ FAILED: Large dataset import did not work as expected")
            return False

    def test_error_handling_in_simplified_mode(self):
        """Test error handling in simplified import mode"""
        print("\n🔍 TESTING ERROR HANDLING IN SIMPLIFIED MODE")
        print("=" * 60)
        
        # Test with invalid data
        import_data = {
            "data": """Invalid line without proper format
Another bad line
192.168.204.1 validtest validpass CA
More invalid data""",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if not success:
            print("   ❌ FAILED: Import request failed")
            return False
        
        report = response.get('report', {})
        testing_mode = report.get('testing_mode')
        session_id = response.get('session_id')
        added = report.get('added', 0)
        format_errors = report.get('format_errors', 0)
        
        print(f"   Nodes added: {added}")
        print(f"   Format errors: {format_errors}")
        print(f"   Testing mode: {testing_mode}")
        print(f"   Session ID: {session_id}")
        
        if (testing_mode == 'no_test' and 
            session_id is None and 
            added >= 1 and 
            format_errors >= 2):
            print("   ✅ SUCCESS: Error handling works correctly in simplified mode")
            return True
        else:
            print("   ❌ FAILED: Error handling not working as expected")
            return False

    def run_additional_tests(self):
        """Run all additional tests"""
        print("🚀 RUNNING ADDITIONAL SIMPLIFIED IMPORT TESTS")
        print("=" * 80)
        
        if not self.test_login():
            print("❌ Cannot proceed without login")
            return False
        
        tests = [
            self.test_backend_hardcoded_no_test,
            self.test_no_background_testing_processes,
            self.test_progress_endpoint_not_created,
            self.test_import_with_large_dataset,
            self.test_error_handling_in_simplified_mode
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                    print("   ✅ PASSED\n")
                else:
                    print("   ❌ FAILED\n")
            except Exception as e:
                print(f"   ❌ CRASHED: {str(e)}\n")
        
        print("=" * 80)
        print(f"ADDITIONAL TESTS SUMMARY: {passed}/{total} passed ({passed/total*100:.1f}%)")
        print("=" * 80)
        
        return passed == total

if __name__ == "__main__":
    tester = AdditionalImportTester()
    success = tester.run_additional_tests()
    sys.exit(0 if success else 1)