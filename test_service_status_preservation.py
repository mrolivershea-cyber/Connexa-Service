#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class ServiceStatusPreservationTester:
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

    def get_or_create_speed_ok_nodes(self, count: int):
        """Helper method to get or create nodes with speed_ok status"""
        # First, try to get existing speed_ok nodes
        success, response = self.make_request('GET', f'nodes?status=speed_ok&limit={count}')
        
        if success and 'nodes' in response and len(response['nodes']) >= count:
            return response['nodes'][:count]
        
        # If not enough speed_ok nodes, try to get some from other statuses and convert them
        print(f"🔄 Looking for nodes to convert to speed_ok status...")
        
        # Try to get ping_ok nodes first
        success, response = self.make_request('GET', f'nodes?status=ping_ok&limit={count}')
        
        if success and 'nodes' in response and response['nodes']:
            ping_ok_nodes = response['nodes'][:count]
            node_ids = [node['id'] for node in ping_ok_nodes]
            
            # Convert ping_ok to speed_ok via speed test
            speed_data = {"node_ids": node_ids}
            speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
            
            if speed_success and 'results' in speed_response:
                speed_ok_node_ids = [r['node_id'] for r in speed_response['results'] if r.get('status') == 'speed_ok']
                
                if speed_ok_node_ids:
                    # Get the updated node objects
                    speed_ok_nodes = []
                    for node_id in speed_ok_node_ids:
                        node_success, node_response = self.make_request('GET', f'nodes?id={node_id}')
                        if node_success and 'nodes' in node_response and node_response['nodes']:
                            speed_ok_nodes.append(node_response['nodes'][0])
                    
                    print(f"✅ Converted {len(speed_ok_nodes)} ping_ok nodes to speed_ok")
                    return speed_ok_nodes
        
        # Try to get not_tested nodes and run full workflow
        success, response = self.make_request('GET', f'nodes?status=not_tested&limit={count}')
        
        if success and 'nodes' in response and response['nodes']:
            not_tested_nodes = response['nodes'][:count]
            node_ids = [node['id'] for node in not_tested_nodes]
            
            print(f"🔄 Running full workflow on {len(node_ids)} not_tested nodes...")
            
            # Step 1: Ping test
            ping_data = {"node_ids": node_ids}
            ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
            
            if ping_success and 'results' in ping_response:
                ping_ok_nodes = [r['node_id'] for r in ping_response['results'] if r.get('status') == 'ping_ok']
                
                if ping_ok_nodes:
                    # Step 2: Speed test
                    speed_data = {"node_ids": ping_ok_nodes}
                    speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
                    
                    if speed_success and 'results' in speed_response:
                        speed_ok_node_ids = [r['node_id'] for r in speed_response['results'] if r.get('status') == 'speed_ok']
                        
                        if speed_ok_node_ids:
                            # Get the updated node objects
                            speed_ok_nodes = []
                            for node_id in speed_ok_node_ids:
                                node_success, node_response = self.make_request('GET', f'nodes?id={node_id}')
                                if node_success and 'nodes' in node_response and node_response['nodes']:
                                    speed_ok_nodes.append(node_response['nodes'][0])
                            
                            print(f"✅ Created {len(speed_ok_nodes)} speed_ok nodes via full workflow")
                            return speed_ok_nodes
        
        print(f"❌ Could not create enough speed_ok nodes")
        return []

    def test_service_status_preservation_start_services(self):
        """CRITICAL TEST: Service Status Preservation for /api/services/start (Green Button)"""
        print("\n🔥 CRITICAL TEST: Service Status Preservation - /api/services/start")
        print("=" * 70)
        
        # Step 1: Get or create nodes with speed_ok status
        speed_ok_nodes = self.get_or_create_speed_ok_nodes(2)
        
        if not speed_ok_nodes:
            self.log_test("Service Status Preservation - Start Services", False, 
                         "No speed_ok nodes available for testing")
            return False
        
        node_ids = [node['id'] for node in speed_ok_nodes]
        
        print(f"📋 Testing with {len(speed_ok_nodes)} speed_ok nodes:")
        for i, node in enumerate(speed_ok_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Step 2: Record initial status
        initial_statuses = {}
        for node in speed_ok_nodes:
            initial_statuses[node['id']] = node['status']
        
        # Step 3: Call /api/services/start (the green button endpoint)
        service_data = {
            "node_ids": node_ids,
            "action": "start"
        }
        
        success, response = self.make_request('POST', 'services/start', service_data)
        
        if not success or 'results' not in response:
            self.log_test("Service Status Preservation - Start Services", False, 
                         f"Service start request failed: {response}")
            return False
        
        # Step 4: Analyze results and verify status preservation
        preserved_count = 0
        downgraded_count = 0
        successful_launches = 0
        
        for result in response['results']:
            node_id = result['node_id']
            initial_status = initial_statuses.get(node_id)
            final_status = result.get('status')
            success_flag = result.get('success', False)
            
            print(f"   Node {node_id}: {initial_status} → {final_status} (Success: {success_flag})")
            print(f"      Message: {result.get('message', 'No message')}")
            
            if success_flag:
                successful_launches += 1
            else:
                # This is the critical test - failed service launches should preserve speed_ok status
                if initial_status == 'speed_ok' and final_status == 'speed_ok':
                    preserved_count += 1
                    print(f"      ✅ PRESERVED: speed_ok status maintained after service failure")
                elif initial_status == 'speed_ok' and final_status in ['ping_failed', 'offline']:
                    downgraded_count += 1
                    print(f"      ❌ DOWNGRADED: speed_ok → {final_status} (BUG!)")
        
        # Step 5: Verify nodes in database
        print(f"\n🔍 Database Verification:")
        db_preserved_count = 0
        db_downgraded_count = 0
        
        for node_id in node_ids:
            db_success, db_response = self.make_request('GET', f'nodes?id={node_id}')
            if db_success and 'nodes' in db_response and db_response['nodes']:
                db_node = db_response['nodes'][0]
                db_status = db_node.get('status')
                initial_status = initial_statuses.get(node_id)
                
                print(f"   Node {node_id}: DB status = {db_status}")
                
                if initial_status == 'speed_ok' and db_status == 'speed_ok':
                    db_preserved_count += 1
                elif initial_status == 'speed_ok' and db_status in ['ping_failed', 'offline']:
                    db_downgraded_count += 1
        
        # Step 6: Final assessment
        total_nodes = len(node_ids)
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   Total nodes tested: {total_nodes}")
        print(f"   Successful service launches: {successful_launches}")
        print(f"   Failed launches with preserved status: {preserved_count}")
        print(f"   Failed launches with downgraded status: {downgraded_count}")
        print(f"   Database preserved count: {db_preserved_count}")
        print(f"   Database downgraded count: {db_downgraded_count}")
        
        # CRITICAL: The fix should ensure NO speed_ok nodes are downgraded on service failure
        if db_downgraded_count == 0 and (preserved_count > 0 or successful_launches > 0):
            self.log_test("Service Status Preservation - Start Services", True, 
                         f"✅ CRITICAL FIX VERIFIED: No speed_ok nodes downgraded. Preserved: {db_preserved_count}, Successful: {successful_launches}")
            return True
        else:
            self.log_test("Service Status Preservation - Start Services", False, 
                         f"❌ CRITICAL BUG: {db_downgraded_count} speed_ok nodes were downgraded to ping_failed/offline")
            return False
    
    def test_service_status_preservation_launch_services(self):
        """CRITICAL TEST: Service Status Preservation for /api/manual/launch-services (Purple Button)"""
        print("\n🔥 CRITICAL TEST: Service Status Preservation - /api/manual/launch-services")
        print("=" * 70)
        
        # Step 1: Get or create nodes with speed_ok status
        speed_ok_nodes = self.get_or_create_speed_ok_nodes(2)
        
        if not speed_ok_nodes:
            self.log_test("Service Status Preservation - Launch Services", False, 
                         "No speed_ok nodes available for testing")
            return False
        
        node_ids = [node['id'] for node in speed_ok_nodes]
        
        print(f"📋 Testing with {len(speed_ok_nodes)} speed_ok nodes:")
        for i, node in enumerate(speed_ok_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Step 2: Record initial status
        initial_statuses = {}
        for node in speed_ok_nodes:
            initial_statuses[node['id']] = node['status']
        
        # Step 3: Call /api/manual/launch-services (the purple button endpoint)
        service_data = {
            "node_ids": node_ids
        }
        
        success, response = self.make_request('POST', 'manual/launch-services', service_data)
        
        if not success or 'results' not in response:
            self.log_test("Service Status Preservation - Launch Services", False, 
                         f"Service launch request failed: {response}")
            return False
        
        # Step 4: Analyze results and verify status preservation
        preserved_count = 0
        downgraded_count = 0
        successful_launches = 0
        
        for result in response['results']:
            node_id = result['node_id']
            initial_status = initial_statuses.get(node_id)
            final_status = result.get('status')
            success_flag = result.get('success', False)
            
            print(f"   Node {node_id}: {initial_status} → {final_status} (Success: {success_flag})")
            print(f"      Message: {result.get('message', 'No message')}")
            
            if success_flag and final_status == 'online':
                successful_launches += 1
            else:
                # This is the critical test - failed service launches should preserve speed_ok status
                if initial_status == 'speed_ok' and final_status == 'speed_ok':
                    preserved_count += 1
                    print(f"      ✅ PRESERVED: speed_ok status maintained after service failure")
                elif initial_status == 'speed_ok' and final_status in ['ping_failed', 'offline']:
                    downgraded_count += 1
                    print(f"      ❌ DOWNGRADED: speed_ok → {final_status} (BUG!)")
        
        # Step 5: Verify nodes in database
        print(f"\n🔍 Database Verification:")
        db_preserved_count = 0
        db_downgraded_count = 0
        
        for node_id in node_ids:
            db_success, db_response = self.make_request('GET', f'nodes?id={node_id}')
            if db_success and 'nodes' in db_response and db_response['nodes']:
                db_node = db_response['nodes'][0]
                db_status = db_node.get('status')
                initial_status = initial_statuses.get(node_id)
                
                print(f"   Node {node_id}: DB status = {db_status}")
                
                if initial_status == 'speed_ok' and db_status == 'speed_ok':
                    db_preserved_count += 1
                elif initial_status == 'speed_ok' and db_status in ['ping_failed', 'offline']:
                    db_downgraded_count += 1
        
        # Step 6: Final assessment
        total_nodes = len(node_ids)
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   Total nodes tested: {total_nodes}")
        print(f"   Successful service launches: {successful_launches}")
        print(f"   Failed launches with preserved status: {preserved_count}")
        print(f"   Failed launches with downgraded status: {downgraded_count}")
        print(f"   Database preserved count: {db_preserved_count}")
        print(f"   Database downgraded count: {db_downgraded_count}")
        
        # CRITICAL: The fix should ensure NO speed_ok nodes are downgraded on service failure
        if db_downgraded_count == 0 and (preserved_count > 0 or successful_launches > 0):
            self.log_test("Service Status Preservation - Launch Services", True, 
                         f"✅ CRITICAL FIX VERIFIED: No speed_ok nodes downgraded. Preserved: {db_preserved_count}, Successful: {successful_launches}")
            return True
        else:
            self.log_test("Service Status Preservation - Launch Services", False, 
                         f"❌ CRITICAL BUG: {db_downgraded_count} speed_ok nodes were downgraded to ping_failed/offline")
            return False

    def test_status_validation_before_after(self):
        """CRITICAL TEST: Status validation before and after service operations"""
        print("\n🔥 CRITICAL TEST: Status Validation Before/After Service Operations")
        print("=" * 70)
        
        # Get current speed_ok count
        before_success, before_response = self.make_request('GET', 'stats')
        
        if not before_success or 'speed_ok' not in before_response:
            self.log_test("Status Validation Before/After", False, 
                         f"Failed to get initial stats: {before_response}")
            return False
        
        initial_speed_ok_count = before_response['speed_ok']
        print(f"📊 Initial speed_ok count: {initial_speed_ok_count}")
        
        # Get some speed_ok nodes for testing
        speed_ok_nodes = self.get_or_create_speed_ok_nodes(3)
        
        if not speed_ok_nodes:
            self.log_test("Status Validation Before/After", False, 
                         "No speed_ok nodes available for testing")
            return False
        
        node_ids = [node['id'] for node in speed_ok_nodes]
        
        # Test both service endpoints
        print(f"\n🔄 Testing service operations with {len(node_ids)} nodes...")
        
        # Test /api/services/start
        start_data = {"node_ids": node_ids[:2], "action": "start"}
        start_success, start_response = self.make_request('POST', 'services/start', start_data)
        
        # Test /api/manual/launch-services
        if len(node_ids) > 2:
            launch_data = {"node_ids": node_ids[2:3]}
            launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
        
        # Get final speed_ok count
        after_success, after_response = self.make_request('GET', 'stats')
        
        if not after_success or 'speed_ok' not in after_response:
            self.log_test("Status Validation Before/After", False, 
                         f"Failed to get final stats: {after_response}")
            return False
        
        final_speed_ok_count = after_response['speed_ok']
        print(f"📊 Final speed_ok count: {final_speed_ok_count}")
        
        # Calculate the change
        speed_ok_change = final_speed_ok_count - initial_speed_ok_count
        
        print(f"\n📊 STATUS COUNT ANALYSIS:")
        print(f"   Initial speed_ok: {initial_speed_ok_count}")
        print(f"   Final speed_ok: {final_speed_ok_count}")
        print(f"   Change: {speed_ok_change:+d}")
        
        # The speed_ok count should not decrease (nodes should not be downgraded)
        # It can stay the same (if services fail but status is preserved) or increase (if new nodes reach speed_ok)
        if speed_ok_change >= 0:
            self.log_test("Status Validation Before/After", True, 
                         f"✅ SPEED_OK COUNT PRESERVED OR INCREASED: {speed_ok_change:+d}")
            return True
        else:
            self.log_test("Status Validation Before/After", False, 
                         f"❌ SPEED_OK COUNT DECREASED: {speed_ok_change} (indicates status downgrade bug)")
            return False

    def run_all_tests(self):
        """Run all critical service status preservation tests"""
        print(f"\n🔥 CRITICAL SERVICE STATUS PRESERVATION TESTING")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 80)
        print("TESTING THE CRITICAL BUG FIX:")
        print("- Users were using 'Start Services' button (/api/services/start) instead of 'Launch Services'")
        print("- The /api/services/start function was downgrading speed_ok nodes to offline/ping_failed on failure")
        print("- JUST IMPLEMENTED FIXES should preserve speed_ok status when service launch fails")
        print("=" * 80)
        
        # Authentication first
        if not self.test_login():
            print("❌ Login failed - cannot continue with tests")
            return False
        
        # Run the critical tests
        self.test_service_status_preservation_start_services()
        self.test_service_status_preservation_launch_services()
        self.test_status_validation_before_after()
        
        # Final summary
        print("\n" + "=" * 80)
        print(f"🏁 CRITICAL SERVICE STATUS PRESERVATION TEST SUMMARY")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL CRITICAL TESTS PASSED - SERVICE STATUS PRESERVATION FIX VERIFIED!")
            return True
        else:
            print("❌ CRITICAL TESTS FAILED - SERVICE STATUS PRESERVATION BUG STILL EXISTS!")
            return False

def main():
    """Main function - run critical service status preservation tests"""
    tester = ServiceStatusPreservationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())