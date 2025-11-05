#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class ServiceManagementTester:
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

    def test_get_stats(self):
        """Test getting statistics to understand current database state"""
        success, response = self.make_request('GET', 'stats')
        
        if success and 'total' in response:
            print(f"\n📊 Current Database State:")
            print(f"   Total nodes: {response.get('total', 0)}")
            print(f"   Not tested: {response.get('not_tested', 0)}")
            print(f"   Ping failed: {response.get('ping_failed', 0)}")
            print(f"   Ping OK: {response.get('ping_ok', 0)}")
            print(f"   Speed slow: {response.get('speed_slow', 0)}")
            print(f"   Speed OK: {response.get('speed_ok', 0)}")
            print(f"   Offline: {response.get('offline', 0)}")
            print(f"   Online: {response.get('online', 0)}")
            
            self.log_test("Get Statistics", True)
            return response
        else:
            self.log_test("Get Statistics", False, f"Failed to get stats: {response}")
            return None

    def test_manual_ping_test(self):
        """Test manual ping test functionality"""
        print(f"\n🏓 TESTING MANUAL PING TEST")
        print("=" * 40)
        
        # Get nodes with 'not_tested' status
        success, response = self.make_request('GET', 'nodes?status=not_tested&limit=3')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Manual Ping Test - Get not_tested nodes", False, 
                         f"No not_tested nodes available: {response}")
            return False
        
        test_nodes = response['nodes'][:2]  # Use first 2 nodes
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Selected {len(test_nodes)} nodes for ping testing:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Perform manual ping test
        ping_data = {"node_ids": node_ids}
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
        
        if ping_success and 'results' in ping_response:
            print(f"\n🏓 Ping Test Results:")
            ping_ok_count = 0
            ping_failed_count = 0
            
            for result in ping_response['results']:
                node_id = result['node_id']
                status = result.get('status', 'unknown')
                message = result.get('message', 'No message')
                success = result.get('success', False)
                
                print(f"   Node {node_id}: {message} (Status: {status}, Success: {success})")
                
                if status == 'ping_ok':
                    ping_ok_count += 1
                elif status == 'ping_failed':
                    ping_failed_count += 1
            
            print(f"   Summary: {ping_ok_count} ping_ok, {ping_failed_count} ping_failed")
            
            self.log_test("Manual Ping Test", True, 
                         f"Ping test completed: {ping_ok_count} OK, {ping_failed_count} failed")
            return ping_response['results']
        else:
            self.log_test("Manual Ping Test", False, f"Ping test failed: {ping_response}")
            return []

    def test_manual_speed_test(self):
        """Test manual speed test functionality"""
        print(f"\n🚀 TESTING MANUAL SPEED TEST")
        print("=" * 40)
        
        # Get nodes with 'ping_ok' status
        success, response = self.make_request('GET', 'nodes?status=ping_ok&limit=2')
        
        if not success or 'nodes' not in response or not response['nodes']:
            # If no ping_ok nodes, create one by setting a node to ping_ok status
            print("   No ping_ok nodes found, creating test node...")
            
            # Get a not_tested node and set it to ping_ok
            success, response = self.make_request('GET', 'nodes?status=not_tested&limit=1')
            if success and 'nodes' in response and response['nodes']:
                test_node = response['nodes'][0]
                node_id = test_node['id']
                
                # Update node to ping_ok status
                update_data = {"status": "ping_ok"}
                update_success, update_response = self.make_request('PUT', f'nodes/{node_id}', update_data)
                
                if update_success:
                    print(f"   Set node {node_id} to ping_ok status")
                    test_nodes = [test_node]
                    test_nodes[0]['status'] = 'ping_ok'
                else:
                    self.log_test("Manual Speed Test - Setup", False, "Could not create ping_ok node")
                    return []
            else:
                self.log_test("Manual Speed Test - Get ping_ok nodes", False, 
                             f"No ping_ok nodes available: {response}")
                return []
        else:
            test_nodes = response['nodes'][:1]  # Use first node
        
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Selected {len(test_nodes)} nodes for speed testing:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Perform manual speed test
        speed_data = {"node_ids": node_ids}
        speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
        
        if speed_success and 'results' in speed_response:
            print(f"\n🚀 Speed Test Results:")
            speed_ok_count = 0
            speed_slow_count = 0
            
            for result in speed_response['results']:
                node_id = result['node_id']
                status = result.get('status', 'unknown')
                message = result.get('message', 'No message')
                success = result.get('success', False)
                speed = result.get('speed', 'N/A')
                
                print(f"   Node {node_id}: {message} (Status: {status}, Speed: {speed}, Success: {success})")
                
                if status == 'speed_ok':
                    speed_ok_count += 1
                elif status == 'speed_slow':
                    speed_slow_count += 1
            
            print(f"   Summary: {speed_ok_count} speed_ok, {speed_slow_count} speed_slow")
            
            self.log_test("Manual Speed Test", True, 
                         f"Speed test completed: {speed_ok_count} OK, {speed_slow_count} slow")
            return speed_response['results']
        else:
            self.log_test("Manual Speed Test", False, f"Speed test failed: {speed_response}")
            return []

    def test_manual_launch_services(self):
        """Test manual launch services functionality"""
        print(f"\n🚀 TESTING MANUAL LAUNCH SERVICES")
        print("=" * 45)
        
        # Get nodes with 'speed_ok' or 'speed_slow' status
        success1, response1 = self.make_request('GET', 'nodes?status=speed_ok&limit=1')
        success2, response2 = self.make_request('GET', 'nodes?status=speed_slow&limit=1')
        
        test_nodes = []
        if success1 and 'nodes' in response1:
            test_nodes.extend(response1['nodes'])
        if success2 and 'nodes' in response2:
            test_nodes.extend(response2['nodes'])
        
        if not test_nodes:
            # If no speed_ok/speed_slow nodes, create one
            print("   No speed_ok/speed_slow nodes found, creating test node...")
            
            # Get a ping_ok node and set it to speed_ok
            success, response = self.make_request('GET', 'nodes?status=ping_ok&limit=1')
            if not success or 'nodes' not in response or not response['nodes']:
                # Create a ping_ok node first
                success, response = self.make_request('GET', 'nodes?status=not_tested&limit=1')
                if success and 'nodes' in response and response['nodes']:
                    test_node = response['nodes'][0]
                    node_id = test_node['id']
                    
                    # Update node to speed_ok status
                    update_data = {"status": "speed_ok"}
                    update_success, update_response = self.make_request('PUT', f'nodes/{node_id}', update_data)
                    
                    if update_success:
                        print(f"   Set node {node_id} to speed_ok status")
                        test_nodes = [test_node]
                        test_nodes[0]['status'] = 'speed_ok'
                    else:
                        self.log_test("Manual Launch Services - Setup", False, "Could not create speed_ok node")
                        return []
                else:
                    self.log_test("Manual Launch Services - Get nodes", False, "No nodes available")
                    return []
            else:
                test_node = response['nodes'][0]
                node_id = test_node['id']
                
                # Update node to speed_ok status
                update_data = {"status": "speed_ok"}
                update_success, update_response = self.make_request('PUT', f'nodes/{node_id}', update_data)
                
                if update_success:
                    print(f"   Set node {node_id} to speed_ok status")
                    test_nodes = [test_node]
                    test_nodes[0]['status'] = 'speed_ok'
                else:
                    self.log_test("Manual Launch Services - Setup", False, "Could not create speed_ok node")
                    return []
        
        node_ids = [node['id'] for node in test_nodes[:1]]  # Use first node
        
        print(f"📋 Selected {len(node_ids)} nodes for service launch testing:")
        for i, node in enumerate(test_nodes[:1], 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Perform manual launch services
        launch_data = {"node_ids": node_ids}
        launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
        
        if launch_success and 'results' in launch_response:
            print(f"\n🚀 Launch Services Results:")
            online_count = 0
            offline_count = 0
            
            for result in launch_response['results']:
                node_id = result['node_id']
                status = result.get('status', 'unknown')
                message = result.get('message', 'No message')
                success = result.get('success', False)
                
                print(f"   Node {node_id}: {message} (Status: {status}, Success: {success})")
                
                if status == 'online':
                    online_count += 1
                elif status == 'offline':
                    offline_count += 1
            
            print(f"   Summary: {online_count} online, {offline_count} offline")
            
            self.log_test("Manual Launch Services", True, 
                         f"Launch services completed: {online_count} online, {offline_count} offline")
            return launch_response['results']
        else:
            self.log_test("Manual Launch Services", False, f"Launch services failed: {launch_response}")
            return []

    def test_services_start_stop(self):
        """Test services start/stop functionality with correct API format"""
        print(f"\n🔧 TESTING SERVICES START/STOP")
        print("=" * 35)
        
        # Get some nodes to test with
        success, response = self.make_request('GET', 'nodes?limit=2')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Services Start/Stop - Get nodes", False, "No nodes available")
            return False
        
        test_nodes = response['nodes'][:1]  # Use first node
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Selected {len(test_nodes)} nodes for start/stop testing:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Test Start Services (with correct format)
        print(f"\n🚀 Testing Start Services")
        start_data = {
            "node_ids": node_ids,
            "action": "start"
        }
        start_success, start_response = self.make_request('POST', 'services/start', start_data)
        
        if start_success and 'results' in start_response:
            print(f"   Start Services API Response: SUCCESS")
            for result in start_response['results']:
                node_id = result['node_id']
                success = result.get('success', False)
                message = result.get('message', 'No message')
                print(f"   Node {node_id}: {message} (Success: {success})")
            
            start_ok = True
        else:
            print(f"   Start Services API Response: FAILED - {start_response}")
            start_ok = False
        
        # Test Stop Services (with correct format)
        print(f"\n🛑 Testing Stop Services")
        stop_data = {
            "node_ids": node_ids,
            "action": "stop"
        }
        stop_success, stop_response = self.make_request('POST', 'services/stop', stop_data)
        
        if stop_success and 'results' in stop_response:
            print(f"   Stop Services API Response: SUCCESS")
            for result in stop_response['results']:
                node_id = result['node_id']
                success = result.get('success', False)
                message = result.get('message', 'No message')
                print(f"   Node {node_id}: {message} (Success: {success})")
            
            stop_ok = True
        else:
            print(f"   Stop Services API Response: FAILED - {stop_response}")
            stop_ok = False
        
        # Overall assessment
        if start_ok and stop_ok:
            self.log_test("Services Start/Stop", True, "Both start and stop services APIs working")
            return True
        else:
            self.log_test("Services Start/Stop", False, f"Start OK: {start_ok}, Stop OK: {stop_ok}")
            return False

    def test_status_transition_workflow(self):
        """Test complete status transition workflow"""
        print(f"\n🔄 TESTING STATUS TRANSITION WORKFLOW")
        print("=" * 45)
        
        # Get a not_tested node
        success, response = self.make_request('GET', 'nodes?status=not_tested&limit=1')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Status Transition Workflow", False, "No not_tested nodes available")
            return False
        
        test_node = response['nodes'][0]
        node_id = test_node['id']
        
        print(f"📋 Testing workflow with Node {node_id}: {test_node['ip']}")
        
        workflow_steps = []
        
        # Step 1: not_tested → ping test → ping_ok/ping_failed
        print(f"\n   Step 1: not_tested → ping test")
        ping_data = {"node_ids": [node_id]}
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
        
        if ping_success and 'results' in ping_response:
            result = ping_response['results'][0]
            new_status = result.get('status')
            print(f"   Result: not_tested → {new_status}")
            workflow_steps.append(f"not_tested → {new_status}")
            
            if new_status == 'ping_ok':
                # Step 2: ping_ok → speed test → speed_ok/speed_slow
                print(f"\n   Step 2: ping_ok → speed test")
                speed_data = {"node_ids": [node_id]}
                speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
                
                if speed_success and 'results' in speed_response:
                    result = speed_response['results'][0]
                    new_status = result.get('status')
                    print(f"   Result: ping_ok → {new_status}")
                    workflow_steps.append(f"ping_ok → {new_status}")
                    
                    if new_status in ['speed_ok', 'speed_slow']:
                        # Step 3: speed_ok/speed_slow → launch services → online/offline
                        print(f"\n   Step 3: {new_status} → launch services")
                        launch_data = {"node_ids": [node_id]}
                        launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
                        
                        if launch_success and 'results' in launch_response:
                            result = launch_response['results'][0]
                            final_status = result.get('status')
                            print(f"   Result: {new_status} → {final_status}")
                            workflow_steps.append(f"{new_status} → {final_status}")
                        else:
                            print(f"   Launch services failed: {launch_response}")
                    else:
                        print(f"   Speed test resulted in {new_status}, cannot proceed to launch services")
                else:
                    print(f"   Speed test failed: {speed_response}")
            else:
                print(f"   Ping test resulted in {new_status}, cannot proceed to speed test")
        else:
            print(f"   Ping test failed: {ping_response}")
        
        print(f"\n   Complete workflow: {' → '.join(workflow_steps)}")
        
        if len(workflow_steps) >= 1:
            self.log_test("Status Transition Workflow", True, 
                         f"Workflow completed: {' → '.join(workflow_steps)}")
            return True
        else:
            self.log_test("Status Transition Workflow", False, "No workflow steps completed")
            return False

    def test_timestamp_updates(self):
        """Test that timestamps are updated correctly"""
        print(f"\n🕐 TESTING TIMESTAMP UPDATES")
        print("=" * 30)
        
        # Get a node and check its timestamp before and after a status change
        success, response = self.make_request('GET', 'nodes?status=not_tested&limit=1')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Timestamp Updates", False, "No not_tested nodes available")
            return False
        
        test_node = response['nodes'][0]
        node_id = test_node['id']
        initial_timestamp = test_node.get('last_update')
        
        print(f"📋 Testing with Node {node_id}: {test_node['ip']}")
        print(f"   Initial timestamp: {initial_timestamp}")
        
        # Wait a moment and perform a ping test
        import time
        time.sleep(2)
        
        ping_data = {"node_ids": [node_id]}
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
        
        if ping_success:
            # Get the updated node
            success, response = self.make_request('GET', f'nodes?id={node_id}')
            
            if success and 'nodes' in response and response['nodes']:
                updated_node = response['nodes'][0]
                new_timestamp = updated_node.get('last_update')
                
                print(f"   Updated timestamp: {new_timestamp}")
                
                if new_timestamp and initial_timestamp and new_timestamp != initial_timestamp:
                    # Parse timestamps to verify the new one is more recent
                    try:
                        from datetime import datetime
                        import dateutil.parser
                        
                        initial_dt = dateutil.parser.parse(initial_timestamp)
                        new_dt = dateutil.parser.parse(new_timestamp)
                        
                        if new_dt > initial_dt:
                            time_diff = (new_dt - initial_dt).total_seconds()
                            print(f"   Timestamp updated correctly (+{time_diff:.1f}s)")
                            
                            self.log_test("Timestamp Updates", True, 
                                         f"Timestamp updated from {initial_timestamp} to {new_timestamp}")
                            return True
                        else:
                            self.log_test("Timestamp Updates", False, 
                                         f"New timestamp is not more recent: {initial_timestamp} → {new_timestamp}")
                            return False
                    except Exception as e:
                        self.log_test("Timestamp Updates", False, f"Timestamp parsing error: {e}")
                        return False
                else:
                    self.log_test("Timestamp Updates", False, 
                                 f"Timestamp not updated: {initial_timestamp} → {new_timestamp}")
                    return False
            else:
                self.log_test("Timestamp Updates", False, "Could not retrieve updated node")
                return False
        else:
            self.log_test("Timestamp Updates", False, f"Ping test failed: {ping_response}")
            return False

def main():
    """Run service management tests"""
    tester = ServiceManagementTester()
    
    print("🔥 CONNEXA SERVICE MANAGEMENT TESTS")
    print("="*80)
    print("Testing critical service management functions as requested in review:")
    print("- Start Services (POST /api/services/start)")
    print("- Stop Services (POST /api/services/stop)")
    print("- Ping Test (POST /api/manual/ping-test)")
    print("- Speed Test (POST /api/manual/speed-test)")
    print("- Launch Services (POST /api/manual/launch-services)")
    print("- Status transition workflow validation")
    print("- Timestamp updates verification")
    print("="*80)
    
    # Authentication
    if not tester.test_login():
        print("❌ Login failed - cannot continue tests")
        return 1
    
    # Get current database state
    stats = tester.test_get_stats()
    
    # Test 1: Manual Ping Test
    tester.test_manual_ping_test()
    
    # Test 2: Manual Speed Test
    tester.test_manual_speed_test()
    
    # Test 3: Manual Launch Services
    tester.test_manual_launch_services()
    
    # Test 4: Services Start/Stop
    tester.test_services_start_stop()
    
    # Test 5: Status Transition Workflow
    tester.test_status_transition_workflow()
    
    # Test 6: Timestamp Updates
    tester.test_timestamp_updates()
    
    # Final summary
    print("\n" + "=" * 80)
    print("🏁 SERVICE MANAGEMENT TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All service management tests passed!")
        return 0
    else:
        print("❌ Some service management tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())