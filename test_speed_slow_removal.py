#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class SpeedSlowRemovalTester:
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

    def test_speed_slow_removal_verification(self):
        """CRITICAL TEST: Verify speed_slow status has been completely removed"""
        print("\n🔥 CRITICAL TEST: SPEED_SLOW REMOVAL VERIFICATION")
        print("=" * 60)
        
        # Test 1: Verify /api/stats does NOT return speed_slow field
        print("📊 TEST 1: Stats API should NOT contain speed_slow field")
        success, response = self.make_request('GET', 'stats')
        
        if success:
            if 'speed_slow' in response:
                self.log_test("Stats API - speed_slow removal", False, 
                             f"❌ CRITICAL: speed_slow field still present in stats: {response}")
                return False
            else:
                self.log_test("Stats API - speed_slow removal", True, 
                             f"✅ speed_slow field correctly removed from stats")
                print(f"   Current stats fields: {list(response.keys())}")
        else:
            self.log_test("Stats API - speed_slow removal", False, f"Failed to get stats: {response}")
            return False
        
        # Test 2: Create test nodes and verify speed test logic
        print("\n🚀 TEST 2: Speed test should set ping_failed instead of speed_slow")
        
        # Create test nodes with not_tested status
        test_nodes_data = [
            {
                "ip": "192.168.100.1",
                "login": "speedtest1",
                "password": "testpass123",
                "protocol": "pptp",
                "comment": "Speed slow removal test node 1"
            },
            {
                "ip": "192.168.100.2", 
                "login": "speedtest2",
                "password": "testpass456",
                "protocol": "pptp",
                "comment": "Speed slow removal test node 2"
            }
        ]
        
        created_node_ids = []
        for node_data in test_nodes_data:
            success, response = self.make_request('POST', 'nodes', node_data)
            if success and 'id' in response:
                created_node_ids.append(response['id'])
                print(f"   Created test node {response['id']}: {node_data['ip']}")
        
        if len(created_node_ids) < 2:
            self.log_test("Speed test logic - node creation", False, 
                         "Failed to create test nodes")
            return False
        
        # Step 1: Manual ping test (not_tested → ping_ok)
        print("   Step 1: Manual ping test...")
        ping_data = {"node_ids": created_node_ids}
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
        
        if not ping_success or 'results' not in ping_response:
            self.log_test("Speed test logic - ping test", False, 
                         f"Ping test failed: {ping_response}")
            return False
        
        ping_ok_nodes = []
        for result in ping_response['results']:
            if result.get('success') and result.get('status') == 'ping_ok':
                ping_ok_nodes.append(result['node_id'])
        
        if not ping_ok_nodes:
            self.log_test("Speed test logic - ping test", False, 
                         "No nodes passed ping test")
            return False
        
        print(f"   Ping test completed: {len(ping_ok_nodes)} nodes now ping_ok")
        
        # Step 2: Manual speed test (ping_ok → speed_ok/ping_failed, NOT speed_slow)
        print("   Step 2: Manual speed test...")
        speed_data = {"node_ids": ping_ok_nodes}
        speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
        
        if not speed_success or 'results' not in speed_response:
            self.log_test("Speed test logic - speed test", False, 
                         f"Speed test failed: {speed_response}")
            return False
        
        # Verify NO node gets speed_slow status
        speed_slow_found = False
        speed_ok_nodes = []
        ping_failed_nodes = []
        
        for result in speed_response['results']:
            node_id = result['node_id']
            status = result.get('status')
            print(f"   Node {node_id}: status = {status}")
            
            if status == 'speed_slow':
                speed_slow_found = True
            elif status == 'speed_ok':
                speed_ok_nodes.append(node_id)
            elif status == 'ping_failed':
                ping_failed_nodes.append(node_id)
        
        if speed_slow_found:
            self.log_test("Speed test logic - no speed_slow", False, 
                         "❌ CRITICAL: speed_slow status still being set by speed test")
            return False
        else:
            self.log_test("Speed test logic - no speed_slow", True, 
                         f"✅ Speed test correctly sets speed_ok ({len(speed_ok_nodes)}) or ping_failed ({len(ping_failed_nodes)}), NO speed_slow")
        
        # Test 3: Manual launch services should only accept speed_ok nodes
        print("\n🚀 TEST 3: Launch services should only accept speed_ok nodes")
        
        if speed_ok_nodes:
            # Test with speed_ok nodes (should work)
            launch_data = {"node_ids": speed_ok_nodes}
            launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
            
            if launch_success and 'results' in launch_response:
                self.log_test("Launch services - accepts speed_ok", True, 
                             f"✅ Launch services correctly accepts speed_ok nodes")
            else:
                self.log_test("Launch services - accepts speed_ok", False, 
                             f"Launch services failed with speed_ok nodes: {launch_response}")
        
        if ping_failed_nodes:
            # Test with ping_failed nodes (should reject)
            launch_data = {"node_ids": ping_failed_nodes}
            launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
            
            if launch_success and 'results' in launch_response:
                # Check if nodes were rejected
                rejected = all(not result.get('success') and 'expected \'speed_ok\'' in result.get('message', '') 
                              for result in launch_response['results'])
                
                if rejected:
                    self.log_test("Launch services - rejects non-speed_ok", True, 
                                 f"✅ Launch services correctly rejects ping_failed nodes")
                else:
                    self.log_test("Launch services - rejects non-speed_ok", False, 
                                 f"Launch services should reject ping_failed nodes")
            else:
                self.log_test("Launch services - rejects non-speed_ok", False, 
                             f"Launch services test failed: {launch_response}")
        
        # Cleanup: Delete test nodes
        print("\n🧹 Cleaning up test nodes...")
        for node_id in created_node_ids:
            self.make_request('DELETE', f'nodes/{node_id}')
        
        print("✅ Speed slow removal verification completed successfully!")
        return True

    def test_status_transition_workflow_new_logic(self):
        """CRITICAL TEST: Verify new status transition workflow without speed_slow"""
        print("\n🔥 CRITICAL TEST: NEW STATUS TRANSITION WORKFLOW")
        print("=" * 60)
        print("Expected workflow:")
        print("  not_tested → (ping test) → ping_ok/ping_failed")
        print("  ping_ok → (speed test) → speed_ok/ping_failed (NOT speed_slow)")
        print("  speed_ok → (launch services) → online/offline")
        
        # Create test node
        test_node = {
            "ip": "192.168.200.1",
            "login": "workflow_test",
            "password": "testpass789",
            "protocol": "pptp",
            "comment": "Status transition workflow test"
        }
        
        success, response = self.make_request('POST', 'nodes', test_node)
        if not success or 'id' not in response:
            self.log_test("Status transition workflow", False, "Failed to create test node")
            return False
        
        node_id = response['id']
        print(f"Created test node {node_id}: {test_node['ip']}")
        
        # Verify initial status is not_tested
        success, response = self.make_request('GET', f'nodes?ip={test_node["ip"]}')
        if success and 'nodes' in response and response['nodes']:
            initial_status = response['nodes'][0]['status']
            if initial_status != 'not_tested':
                self.log_test("Status transition workflow - initial status", False, 
                             f"Expected not_tested, got {initial_status}")
                return False
            print(f"✅ Initial status: {initial_status}")
        
        # Step 1: not_tested → ping_ok/ping_failed
        print("\n📍 Step 1: not_tested → ping test → ping_ok/ping_failed")
        ping_data = {"node_ids": [node_id]}
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
        
        if not ping_success or 'results' not in ping_response:
            self.log_test("Status transition workflow - ping step", False, 
                         f"Ping test failed: {ping_response}")
            return False
        
        ping_result = ping_response['results'][0]
        ping_status = ping_result.get('status')
        print(f"   Ping result: {ping_status}")
        
        if ping_status not in ['ping_ok', 'ping_failed']:
            self.log_test("Status transition workflow - ping step", False, 
                         f"Expected ping_ok or ping_failed, got {ping_status}")
            return False
        
        if ping_status == 'ping_failed':
            print("   Node failed ping test - workflow stops here (as expected)")
            self.log_test("Status transition workflow", True, 
                         "✅ Workflow correctly stops at ping_failed")
            # Cleanup
            self.make_request('DELETE', f'nodes/{node_id}')
            return True
        
        # Step 2: ping_ok → speed_ok/ping_failed (NOT speed_slow)
        print("\n📍 Step 2: ping_ok → speed test → speed_ok/ping_failed")
        speed_data = {"node_ids": [node_id]}
        speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
        
        if not speed_success or 'results' not in speed_response:
            self.log_test("Status transition workflow - speed step", False, 
                         f"Speed test failed: {speed_response}")
            return False
        
        speed_result = speed_response['results'][0]
        speed_status = speed_result.get('status')
        print(f"   Speed result: {speed_status}")
        
        if speed_status == 'speed_slow':
            self.log_test("Status transition workflow - speed step", False, 
                         "❌ CRITICAL: speed_slow status still being set!")
            return False
        
        if speed_status not in ['speed_ok', 'ping_failed']:
            self.log_test("Status transition workflow - speed step", False, 
                         f"Expected speed_ok or ping_failed, got {speed_status}")
            return False
        
        if speed_status == 'ping_failed':
            print("   Node failed speed test → ping_failed (as expected)")
            self.log_test("Status transition workflow", True, 
                         "✅ Workflow correctly sets ping_failed for failed speed test")
            # Cleanup
            self.make_request('DELETE', f'nodes/{node_id}')
            return True
        
        # Step 3: speed_ok → online/offline
        print("\n📍 Step 3: speed_ok → launch services → online/offline")
        launch_data = {"node_ids": [node_id]}
        launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
        
        if not launch_success or 'results' not in launch_response:
            self.log_test("Status transition workflow - launch step", False, 
                         f"Launch services failed: {launch_response}")
            return False
        
        launch_result = launch_response['results'][0]
        final_status = launch_result.get('status', 'unknown')
        print(f"   Launch result: {final_status}")
        
        if final_status not in ['online', 'offline']:
            self.log_test("Status transition workflow - launch step", False, 
                         f"Expected online or offline, got {final_status}")
            return False
        
        print(f"✅ Complete workflow: not_tested → ping_ok → speed_ok → {final_status}")
        self.log_test("Status transition workflow", True, 
                     f"✅ New workflow completed successfully: not_tested → ping_ok → speed_ok → {final_status}")
        
        # Cleanup
        self.make_request('DELETE', f'nodes/{node_id}')
        return True

    def test_database_state_verification(self):
        """Verify current database state matches expected values"""
        print("\n📊 DATABASE STATE VERIFICATION")
        print("=" * 50)
        
        success, response = self.make_request('GET', 'stats')
        if success:
            total = response.get('total', 0)
            not_tested = response.get('not_tested', 0)
            ping_failed = response.get('ping_failed', 0)
            
            print(f"   Total nodes: {total}")
            print(f"   Not tested: {not_tested}")
            print(f"   Ping failed: {ping_failed}")
            
            # Expected: 2349 total nodes, 2335 not_tested, 12 ping_failed
            if total >= 2300 and not_tested >= 2300:
                self.log_test("Database state verification", True, 
                             f"Database state looks correct: {total} total, {not_tested} not_tested, {ping_failed} ping_failed")
                return True
            else:
                self.log_test("Database state verification", False, 
                             f"Unexpected database state: {total} total, {not_tested} not_tested")
                return False
        else:
            self.log_test("Database state verification", False, f"Failed to get stats: {response}")
            return False

    def run_tests(self):
        """Run speed_slow removal tests"""
        print("🔥 SPEED_SLOW REMOVAL VERIFICATION TESTS")
        print("=" * 60)
        print("Testing changes after removing speed_slow status:")
        print("1. API Stats should NOT return speed_slow field")
        print("2. Speed test should set ping_failed instead of speed_slow")
        print("3. Launch services should only accept speed_ok nodes")
        print("4. Status transitions should be: not_tested → ping_ok/ping_failed → speed_ok/ping_failed → online/offline")
        print("=" * 60)
        
        # Login first
        if not self.test_login():
            print("❌ Login failed - cannot continue")
            return False
        
        # Verify database state
        self.test_database_state_verification()
        
        # Run speed_slow removal tests
        self.test_speed_slow_removal_verification()
        self.test_status_transition_workflow_new_logic()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 SPEED_SLOW REMOVAL TEST SUMMARY")
        print("=" * 60)
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run*100):.1f}%)")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Speed_slow removal is working correctly.")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed. Check the details above.")
            return False

def main():
    tester = SpeedSlowRemovalTester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())