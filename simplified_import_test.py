#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class SimplifiedImportTester:
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
        
        if details:
            print(f"   Details: {details}")
        
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

    def test_simplified_import_no_test_mode(self):
        """Test 1: Verify import always uses testing_mode='no_test' regardless of input"""
        print("\n🔍 TEST 1: Simplified Import - Always No Test Mode")
        print("=" * 60)
        
        # Test with different testing_mode values in input - should all be ignored
        test_cases = [
            {"testing_mode": "ping_only", "description": "Input: ping_only"},
            {"testing_mode": "speed_only", "description": "Input: speed_only"}, 
            {"testing_mode": "both", "description": "Input: both"},
            {"testing_mode": "no_test", "description": "Input: no_test"},
            # Test without testing_mode field
            {None: None, "description": "Input: no testing_mode field"}
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test 1.{i}: {test_case['description']}")
            
            # Create unique test data for each case
            import_data = {
                "data": f"""Ip: 192.168.100.{i}
Login: testuser{i}
Pass: testpass{i}
State: California
City: TestCity{i}""",
                "protocol": "pptp"
            }
            
            # Add testing_mode only if it's not None
            if list(test_case.keys())[0] is not None:
                import_data["testing_mode"] = test_case["testing_mode"]
            
            success, response = self.make_request('POST', 'nodes/import', import_data)
            
            if success and 'report' in response:
                report = response['report']
                testing_mode = report.get('testing_mode')
                session_id = response.get('session_id')
                
                # Verify testing_mode is always "no_test"
                if testing_mode == "no_test" and session_id is None:
                    print(f"      ✅ Correct: testing_mode='{testing_mode}', session_id={session_id}")
                else:
                    print(f"      ❌ Wrong: testing_mode='{testing_mode}', session_id={session_id}")
                    all_passed = False
            else:
                print(f"      ❌ Import failed: {response}")
                all_passed = False
        
        self.log_test("Simplified Import - Always No Test Mode", all_passed, 
                     "All import requests forced to testing_mode='no_test' with session_id=None")
        return all_passed

    def test_new_nodes_not_tested_status(self):
        """Test 2: Verify all new nodes get 'not_tested' status"""
        print("\n🔍 TEST 2: New Nodes Get 'not_tested' Status")
        print("=" * 60)
        
        # Import multiple nodes with different formats
        import_data = {
            "data": """Ip: 192.168.101.1
Login: statustest1
Pass: testpass1
State: California

192.168.101.2 statustest2 testpass2 Texas

192.168.101.3:statustest3:testpass3:US:Florida:33101""",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            added_count = report.get('added', 0)
            
            if added_count >= 3:
                # Verify each imported node has 'not_tested' status
                test_ips = ['192.168.101.1', '192.168.101.2', '192.168.101.3']
                all_correct = True
                
                for ip in test_ips:
                    nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                    
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        status = node.get('status')
                        
                        if status == 'not_tested':
                            print(f"   ✅ Node {ip}: status = '{status}' (correct)")
                        else:
                            print(f"   ❌ Node {ip}: status = '{status}' (should be 'not_tested')")
                            all_correct = False
                    else:
                        print(f"   ❌ Node {ip}: not found in database")
                        all_correct = False
                
                self.log_test("New Nodes Get 'not_tested' Status", all_correct,
                             f"All {added_count} imported nodes have 'not_tested' status")
                return all_correct
            else:
                self.log_test("New Nodes Get 'not_tested' Status", False,
                             f"Expected 3 nodes, only {added_count} added")
                return False
        else:
            self.log_test("New Nodes Get 'not_tested' Status", False, f"Import failed: {response}")
            return False

    def test_no_session_id_returned(self):
        """Test 3: Verify session_id is always None (no testing sessions created)"""
        print("\n🔍 TEST 3: No Session ID Returned")
        print("=" * 60)
        
        # Test multiple import scenarios
        test_scenarios = [
            {
                "name": "Single node import",
                "data": "Ip: 192.168.102.1\nLogin: sessiontest1\nPass: testpass1\nState: California"
            },
            {
                "name": "Multiple nodes import", 
                "data": """192.168.102.2 sessiontest2 testpass2 Texas
192.168.102.3 sessiontest3 testpass3 Florida"""
            },
            {
                "name": "Large batch import",
                "data": "\n".join([f"192.168.102.{i} sessiontest{i} testpass{i} CA" for i in range(10, 20)])
            }
        ]
        
        all_passed = True
        
        for scenario in test_scenarios:
            print(f"\n   Testing: {scenario['name']}")
            
            import_data = {
                "data": scenario['data'],
                "protocol": "pptp"
            }
            
            success, response = self.make_request('POST', 'nodes/import', import_data)
            
            if success:
                session_id = response.get('session_id')
                
                if session_id is None:
                    print(f"      ✅ Correct: session_id = {session_id}")
                else:
                    print(f"      ❌ Wrong: session_id = {session_id} (should be None)")
                    all_passed = False
            else:
                print(f"      ❌ Import failed: {response}")
                all_passed = False
        
        self.log_test("No Session ID Returned", all_passed,
                     "All import requests return session_id=None")
        return all_passed

    def test_no_automatic_testing_triggered(self):
        """Test 4: Verify no automatic testing is triggered"""
        print("\n🔍 TEST 4: No Automatic Testing Triggered")
        print("=" * 60)
        
        # Import nodes and verify they remain in 'not_tested' status
        import_data = {
            "data": """Ip: 192.168.103.1
Login: autotest1
Pass: testpass1
State: California

Ip: 192.168.103.2
Login: autotest2
Pass: testpass2
State: Texas""",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            added_count = report.get('added', 0)
            
            if added_count >= 2:
                # Wait a few seconds to see if any automatic testing starts
                print("   Waiting 10 seconds to check for automatic testing...")
                time.sleep(10)
                
                # Check if nodes are still in 'not_tested' status
                test_ips = ['192.168.103.1', '192.168.103.2']
                all_still_not_tested = True
                
                for ip in test_ips:
                    nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                    
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        status = node.get('status')
                        
                        if status == 'not_tested':
                            print(f"   ✅ Node {ip}: still 'not_tested' (no automatic testing)")
                        else:
                            print(f"   ❌ Node {ip}: status changed to '{status}' (automatic testing detected!)")
                            all_still_not_tested = False
                    else:
                        print(f"   ❌ Node {ip}: not found")
                        all_still_not_tested = False
                
                self.log_test("No Automatic Testing Triggered", all_still_not_tested,
                             "All nodes remain 'not_tested' - no automatic testing triggered")
                return all_still_not_tested
            else:
                self.log_test("No Automatic Testing Triggered", False,
                             f"Expected 2 nodes, only {added_count} added")
                return False
        else:
            self.log_test("No Automatic Testing Triggered", False, f"Import failed: {response}")
            return False

    def test_import_response_structure(self):
        """Test 5: Verify import response structure is correct"""
        print("\n🔍 TEST 5: Import Response Structure")
        print("=" * 60)
        
        import_data = {
            "data": """Ip: 192.168.104.1
Login: structest1
Pass: testpass1
State: California""",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success:
            # Check required fields in response
            required_fields = ['success', 'message', 'report', 'session_id']
            missing_fields = []
            
            for field in required_fields:
                if field not in response:
                    missing_fields.append(field)
            
            # Check report structure
            report = response.get('report', {})
            required_report_fields = [
                'total_processed', 'successfully_parsed', 'added', 
                'skipped_duplicates', 'replaced_old', 'queued_for_verification',
                'format_errors', 'processing_errors', 'testing_mode'
            ]
            
            missing_report_fields = []
            for field in required_report_fields:
                if field not in report:
                    missing_report_fields.append(field)
            
            # Verify specific values
            testing_mode = report.get('testing_mode')
            session_id = response.get('session_id')
            
            all_correct = (
                len(missing_fields) == 0 and
                len(missing_report_fields) == 0 and
                testing_mode == 'no_test' and
                session_id is None
            )
            
            if all_correct:
                print("   ✅ All required fields present")
                print(f"   ✅ testing_mode = '{testing_mode}'")
                print(f"   ✅ session_id = {session_id}")
            else:
                if missing_fields:
                    print(f"   ❌ Missing response fields: {missing_fields}")
                if missing_report_fields:
                    print(f"   ❌ Missing report fields: {missing_report_fields}")
                if testing_mode != 'no_test':
                    print(f"   ❌ Wrong testing_mode: '{testing_mode}'")
                if session_id is not None:
                    print(f"   ❌ Wrong session_id: {session_id}")
            
            self.log_test("Import Response Structure", all_correct,
                         "Response contains all required fields with correct values")
            return all_correct
        else:
            self.log_test("Import Response Structure", False, f"Import failed: {response}")
            return False

    def test_manual_testing_still_works(self):
        """Test 6: Verify existing manual testing functionality still works"""
        print("\n🔍 TEST 6: Manual Testing Functionality Still Works")
        print("=" * 60)
        
        # First, create a test node
        import_data = {
            "data": """Ip: 192.168.105.1
Login: manualtest1
Pass: testpass1
State: California""",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if not success or response.get('report', {}).get('added', 0) == 0:
            self.log_test("Manual Testing Functionality", False, "Failed to create test node")
            return False
        
        # Get the created node
        nodes_success, nodes_response = self.make_request('GET', 'nodes?ip=192.168.105.1')
        
        if not nodes_success or not nodes_response.get('nodes'):
            self.log_test("Manual Testing Functionality", False, "Failed to retrieve test node")
            return False
        
        node = nodes_response['nodes'][0]
        node_id = node['id']
        
        # Test manual ping endpoint
        ping_data = {
            "node_ids": [node_id]
        }
        
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
        
        if ping_success and 'results' in ping_response:
            print("   ✅ Manual ping test endpoint working")
            
            # Test manual speed endpoint (should work even if ping fails)
            speed_data = {
                "node_ids": [node_id]
            }
            
            speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
            
            # Speed test might fail due to status requirements, but endpoint should respond
            if speed_success or speed_response.get('status_code') in [400, 422]:
                print("   ✅ Manual speed test endpoint accessible")
                
                # Test manual launch services endpoint
                launch_data = {
                    "node_ids": [node_id]
                }
                
                launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
                
                # Launch might fail due to status requirements, but endpoint should respond
                if launch_success or launch_response.get('status_code') in [400, 422]:
                    print("   ✅ Manual launch services endpoint accessible")
                    
                    self.log_test("Manual Testing Functionality", True,
                                 "All manual testing endpoints are accessible and working")
                    return True
                else:
                    self.log_test("Manual Testing Functionality", False,
                                 f"Launch services endpoint failed: {launch_response}")
                    return False
            else:
                self.log_test("Manual Testing Functionality", False,
                             f"Speed test endpoint failed: {speed_response}")
                return False
        else:
            self.log_test("Manual Testing Functionality", False,
                         f"Ping test endpoint failed: {ping_response}")
            return False

    def test_various_import_data_formats(self):
        """Test 7: Test import with various data formats"""
        print("\n🔍 TEST 7: Various Import Data Formats")
        print("=" * 60)
        
        test_formats = [
            {
                "name": "Format 1 - Key-Value",
                "data": """Ip: 192.168.106.1
Login: format1test
Pass: testpass1
State: California
City: Los Angeles"""
            },
            {
                "name": "Format 2 - Space Separated", 
                "data": "192.168.106.2 format2test testpass2 Texas"
            },
            {
                "name": "Format 3 - Dash Format",
                "data": "192.168.106.3 - format3test:testpass3 - Florida/Miami 33101"
            },
            {
                "name": "Format 4 - Colon Separated",
                "data": "192.168.106.4:format4test:testpass4:US:Nevada:89101"
            }
        ]
        
        all_passed = True
        
        for format_test in test_formats:
            print(f"\n   Testing: {format_test['name']}")
            
            import_data = {
                "data": format_test['data'],
                "protocol": "pptp"
            }
            
            success, response = self.make_request('POST', 'nodes/import', import_data)
            
            if success and 'report' in response:
                report = response['report']
                testing_mode = report.get('testing_mode')
                session_id = response.get('session_id')
                added = report.get('added', 0)
                
                if testing_mode == 'no_test' and session_id is None and added >= 1:
                    print(f"      ✅ Success: added={added}, testing_mode='{testing_mode}', session_id={session_id}")
                else:
                    print(f"      ❌ Failed: added={added}, testing_mode='{testing_mode}', session_id={session_id}")
                    all_passed = False
            else:
                print(f"      ❌ Import failed: {response}")
                all_passed = False
        
        self.log_test("Various Import Data Formats", all_passed,
                     "All data formats work with simplified import (no_test mode)")
        return all_passed

    def test_duplicate_handling(self):
        """Test 8: Test duplicate handling in simplified mode"""
        print("\n🔍 TEST 8: Duplicate Handling in Simplified Mode")
        print("=" * 60)
        
        # First import
        import_data_1 = {
            "data": """Ip: 192.168.107.1
Login: duptest1
Pass: testpass1
State: California""",
            "protocol": "pptp"
        }
        
        success1, response1 = self.make_request('POST', 'nodes/import', import_data_1)
        
        if not success1:
            self.log_test("Duplicate Handling", False, f"First import failed: {response1}")
            return False
        
        # Second import (same data - should be skipped as duplicate)
        success2, response2 = self.make_request('POST', 'nodes/import', import_data_1)
        
        if success2 and 'report' in response2:
            report = response2['report']
            testing_mode = report.get('testing_mode')
            session_id = response2.get('session_id')
            skipped = report.get('skipped_duplicates', 0)
            added = report.get('added', 0)
            
            if testing_mode == 'no_test' and session_id is None and skipped >= 1 and added == 0:
                print(f"   ✅ Duplicate correctly skipped: skipped={skipped}, added={added}")
                print(f"   ✅ Still in simplified mode: testing_mode='{testing_mode}', session_id={session_id}")
                
                self.log_test("Duplicate Handling", True,
                             "Duplicates handled correctly in simplified mode")
                return True
            else:
                self.log_test("Duplicate Handling", False,
                             f"Unexpected results: skipped={skipped}, added={added}, testing_mode='{testing_mode}'")
                return False
        else:
            self.log_test("Duplicate Handling", False, f"Second import failed: {response2}")
            return False

    def run_all_tests(self):
        """Run all simplified import tests"""
        print("🚀 STARTING SIMPLIFIED IMPORT TESTING")
        print("=" * 80)
        print("Testing the simplified import process in Connexa Admin Panel")
        print("URL:", self.base_url)
        print("=" * 80)
        
        # Login first
        if not self.test_login():
            print("❌ Cannot proceed without login")
            return False
        
        # Run all tests
        tests = [
            self.test_simplified_import_no_test_mode,
            self.test_new_nodes_not_tested_status,
            self.test_no_session_id_returned,
            self.test_no_automatic_testing_triggered,
            self.test_import_response_structure,
            self.test_manual_testing_still_works,
            self.test_various_import_data_formats,
            self.test_duplicate_handling
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                self.log_test(test.__name__, False, f"Test crashed: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 SIMPLIFIED IMPORT TESTING SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! Simplified import is working correctly.")
            print("\n✅ VERIFIED REQUIREMENTS:")
            print("   • Import always uses testing_mode='no_test'")
            print("   • All new nodes get 'not_tested' status")
            print("   • No session_id returned (no testing sessions)")
            print("   • No automatic testing triggered")
            print("   • Manual testing endpoints still work")
            print("   • All import formats supported")
            print("   • Duplicate handling works correctly")
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} TESTS FAILED")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = SimplifiedImportTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)