#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class ComprehensiveSpeedSlowTester:
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

    def test_stats_api_no_speed_slow(self):
        """Test 1: Verify /api/stats does NOT return speed_slow field"""
        print("\n📊 TEST 1: Stats API should NOT contain speed_slow field")
        success, response = self.make_request('GET', 'stats')
        
        if success:
            if 'speed_slow' in response:
                self.log_test("Stats API - speed_slow removal", False, 
                             f"❌ CRITICAL: speed_slow field still present in stats")
                return False
            else:
                self.log_test("Stats API - speed_slow removal", True, 
                             f"✅ speed_slow field correctly removed from stats")
                print(f"   Current stats fields: {list(response.keys())}")
                print(f"   Status counts: not_tested={response.get('not_tested', 0)}, ping_failed={response.get('ping_failed', 0)}, ping_ok={response.get('ping_ok', 0)}, speed_ok={response.get('speed_ok', 0)}, offline={response.get('offline', 0)}, online={response.get('online', 0)}")
                return True
        else:
            self.log_test("Stats API - speed_slow removal", False, f"Failed to get stats: {response}")
            return False

    def test_manual_speed_test_api_validation(self):
        """Test 2: Manual speed test API should only accept ping_ok nodes"""
        print("\n🚀 TEST 2: Manual speed test API validation")
        
        # Get some not_tested nodes
        success, response = self.make_request('GET', 'nodes?status=not_tested&limit=2')
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Manual speed test validation", False, "No not_tested nodes found")
            return False
        
        not_tested_node_ids = [node['id'] for node in response['nodes'][:2]]
        print(f"   Testing with not_tested nodes: {not_tested_node_ids}")
        
        # Try speed test on not_tested nodes (should fail)
        speed_data = {"node_ids": not_tested_node_ids}
        speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
        
        if speed_success and 'results' in speed_response:
            # Check that all nodes were rejected
            all_rejected = True
            for result in speed_response['results']:
                if result.get('success') or 'expected \'ping_ok\'' not in result.get('message', ''):
                    all_rejected = False
                    break
            
            if all_rejected:
                self.log_test("Manual speed test validation", True, 
                             "✅ Speed test correctly rejects not_tested nodes")
                return True
            else:
                self.log_test("Manual speed test validation", False, 
                             "Speed test should reject not_tested nodes")
                return False
        else:
            self.log_test("Manual speed test validation", False, 
                         f"Speed test API call failed: {speed_response}")
            return False

    def test_manual_launch_services_api_validation(self):
        """Test 3: Manual launch services should only accept speed_ok nodes"""
        print("\n🚀 TEST 3: Manual launch services API validation")
        
        # Get some not_tested nodes
        success, response = self.make_request('GET', 'nodes?status=not_tested&limit=2')
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Manual launch services validation", False, "No not_tested nodes found")
            return False
        
        not_tested_node_ids = [node['id'] for node in response['nodes'][:2]]
        print(f"   Testing with not_tested nodes: {not_tested_node_ids}")
        
        # Try launch services on not_tested nodes (should fail)
        launch_data = {"node_ids": not_tested_node_ids}
        launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
        
        if launch_success and 'results' in launch_response:
            # Check that all nodes were rejected
            all_rejected = True
            for result in launch_response['results']:
                if result.get('success') or 'expected \'speed_ok\'' not in result.get('message', ''):
                    all_rejected = False
                    break
            
            if all_rejected:
                self.log_test("Manual launch services validation", True, 
                             "✅ Launch services correctly rejects non-speed_ok nodes")
                return True
            else:
                self.log_test("Manual launch services validation", False, 
                             "Launch services should reject non-speed_ok nodes")
                return False
        else:
            self.log_test("Manual launch services validation", False, 
                         f"Launch services API call failed: {launch_response}")
            return False

    def test_status_transition_logic_with_existing_nodes(self):
        """Test 4: Test status transitions with existing nodes"""
        print("\n📍 TEST 4: Status transition logic verification")
        
        # Check if we have any ping_ok nodes
        success, response = self.make_request('GET', 'nodes?status=ping_ok&limit=1')
        if success and 'nodes' in response and response['nodes']:
            ping_ok_node = response['nodes'][0]
            print(f"   Found ping_ok node: {ping_ok_node['id']} ({ping_ok_node['ip']})")
            
            # Try speed test on ping_ok node
            speed_data = {"node_ids": [ping_ok_node['id']]}
            speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
            
            if speed_success and 'results' in speed_response:
                result = speed_response['results'][0]
                final_status = result.get('status')
                print(f"   Speed test result: {final_status}")
                
                # Verify it's NOT speed_slow
                if final_status == 'speed_slow':
                    self.log_test("Status transition logic", False, 
                                 "❌ CRITICAL: speed_slow status still being set!")
                    return False
                elif final_status in ['speed_ok', 'ping_failed']:
                    self.log_test("Status transition logic", True, 
                                 f"✅ Speed test correctly sets {final_status} (NOT speed_slow)")
                    return True
                else:
                    self.log_test("Status transition logic", False, 
                                 f"Unexpected status: {final_status}")
                    return False
            else:
                self.log_test("Status transition logic", False, 
                             f"Speed test failed: {speed_response}")
                return False
        else:
            print("   No ping_ok nodes found - testing with manual ping first")
            
            # Get a not_tested node and try to ping it
            success, response = self.make_request('GET', 'nodes?status=not_tested&limit=1')
            if success and 'nodes' in response and response['nodes']:
                test_node = response['nodes'][0]
                print(f"   Testing with not_tested node: {test_node['id']} ({test_node['ip']})")
                
                # Try ping test
                ping_data = {"node_ids": [test_node['id']]}
                ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
                
                if ping_success and 'results' in ping_response:
                    result = ping_response['results'][0]
                    ping_status = result.get('status')
                    print(f"   Ping test result: {ping_status}")
                    
                    if ping_status in ['ping_ok', 'ping_failed']:
                        self.log_test("Status transition logic", True, 
                                     f"✅ Ping test correctly sets {ping_status}")
                        return True
                    else:
                        self.log_test("Status transition logic", False, 
                                     f"Unexpected ping status: {ping_status}")
                        return False
                else:
                    self.log_test("Status transition logic", False, 
                                 f"Ping test failed: {ping_response}")
                    return False
            else:
                self.log_test("Status transition logic", False, "No nodes available for testing")
                return False

    def test_database_consistency(self):
        """Test 5: Verify database consistency - no speed_slow nodes exist"""
        print("\n🗄️ TEST 5: Database consistency check")
        
        # Try to find any nodes with speed_slow status
        success, response = self.make_request('GET', 'nodes?status=speed_slow&limit=1')
        
        if success:
            if 'nodes' in response and response['nodes']:
                self.log_test("Database consistency", False, 
                             f"❌ CRITICAL: Found {len(response['nodes'])} nodes with speed_slow status")
                return False
            else:
                self.log_test("Database consistency", True, 
                             "✅ No nodes with speed_slow status found in database")
                return True
        else:
            # If the API returns an error, it might be because speed_slow is not a valid status anymore
            if 'status_code' in response and response['status_code'] == 422:
                self.log_test("Database consistency", True, 
                             "✅ API rejects speed_slow as invalid status (good!)")
                return True
            else:
                self.log_test("Database consistency", False, 
                             f"Failed to query database: {response}")
                return False

    def test_workflow_completeness(self):
        """Test 6: Verify complete workflow paths"""
        print("\n🔄 TEST 6: Complete workflow verification")
        
        # Get stats to understand current state
        success, response = self.make_request('GET', 'stats')
        if not success:
            self.log_test("Workflow completeness", False, "Failed to get stats")
            return False
        
        stats = response
        print(f"   Current database state:")
        print(f"   - Total: {stats.get('total', 0)}")
        print(f"   - Not tested: {stats.get('not_tested', 0)}")
        print(f"   - Ping failed: {stats.get('ping_failed', 0)}")
        print(f"   - Ping OK: {stats.get('ping_ok', 0)}")
        print(f"   - Speed OK: {stats.get('speed_ok', 0)}")
        print(f"   - Offline: {stats.get('offline', 0)}")
        print(f"   - Online: {stats.get('online', 0)}")
        
        # Verify expected workflow states exist
        expected_states = ['not_tested', 'ping_failed', 'ping_ok', 'speed_ok', 'offline', 'online']
        missing_states = []
        
        for state in expected_states:
            if state not in stats:
                missing_states.append(state)
        
        # Verify speed_slow is NOT in stats
        if 'speed_slow' in stats:
            self.log_test("Workflow completeness", False, 
                         "❌ CRITICAL: speed_slow still present in stats")
            return False
        
        if missing_states:
            self.log_test("Workflow completeness", False, 
                         f"Missing expected states: {missing_states}")
            return False
        else:
            self.log_test("Workflow completeness", True, 
                         "✅ All expected workflow states present, speed_slow correctly removed")
            return True

    def run_comprehensive_tests(self):
        """Run comprehensive speed_slow removal tests"""
        print("🔥 COMPREHENSIVE SPEED_SLOW REMOVAL VERIFICATION")
        print("=" * 70)
        print("TESTING AFTER SPEED_SLOW STATUS REMOVAL:")
        print("1. ✅ API Stats should NOT return speed_slow field")
        print("2. ✅ Speed test should set ping_failed instead of speed_slow") 
        print("3. ✅ Launch services should only accept speed_ok nodes")
        print("4. ✅ Status transitions: not_tested → ping_ok/ping_failed → speed_ok/ping_failed → online/offline")
        print("5. ✅ Database should contain NO speed_slow nodes")
        print("6. ✅ Complete workflow should work without speed_slow")
        print("=" * 70)
        
        # Login first
        if not self.test_login():
            print("❌ Login failed - cannot continue")
            return False
        
        # Run all tests
        test_results = []
        test_results.append(self.test_stats_api_no_speed_slow())
        test_results.append(self.test_manual_speed_test_api_validation())
        test_results.append(self.test_manual_launch_services_api_validation())
        test_results.append(self.test_status_transition_logic_with_existing_nodes())
        test_results.append(self.test_database_consistency())
        test_results.append(self.test_workflow_completeness())
        
        # Print summary
        print("\n" + "=" * 70)
        print("🏁 COMPREHENSIVE SPEED_SLOW REMOVAL TEST SUMMARY")
        print("=" * 70)
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run*100):.1f}%)")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Speed_slow removal is working correctly.")
            print("\n✅ VERIFICATION COMPLETE:")
            print("   - speed_slow status completely removed from system")
            print("   - Speed test now sets ping_failed instead of speed_slow")
            print("   - Launch services only accepts speed_ok nodes")
            print("   - New workflow: not_tested → ping_ok/ping_failed → speed_ok/ping_failed → online/offline")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} test(s) failed. Check the details above.")
            
            # Show which tests failed
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
            
            return False

def main():
    tester = ComprehensiveSpeedSlowTester()
    success = tester.run_comprehensive_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())