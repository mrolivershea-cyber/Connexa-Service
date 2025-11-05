#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class WorkflowTester:
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

    def make_request(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200):
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

    def test_complete_workflow_with_known_ips(self):
        """Test complete workflow with known working IPs: 72.197.30.147, 100.11.102.204, 100.16.39.213"""
        print("\n🔥 TESTING COMPLETE WORKFLOW WITH KNOWN WORKING IPs")
        print("=" * 60)
        
        # Known working IPs from review request
        known_ips = ["72.197.30.147", "100.11.102.204", "100.16.39.213"]
        
        # First, ensure these IPs exist in database with not_tested status
        for ip in known_ips:
            # Check if node exists
            success, response = self.make_request('GET', f'nodes?ip={ip}')
            
            if not success or 'nodes' not in response or not response['nodes']:
                # Create the node if it doesn't exist
                node_data = {
                    "ip": ip,
                    "login": "admin",
                    "password": "admin",
                    "protocol": "pptp",
                    "status": "not_tested",
                    "provider": "Test Provider",
                    "country": "United States",
                    "state": "California",
                    "city": "Test City"
                }
                create_success, create_response = self.make_request('POST', 'nodes', node_data)
                if not create_success:
                    self.log_test(f"Create Test Node {ip}", False, f"Failed to create: {create_response}")
                    continue
                print(f"   ✅ Created test node: {ip}")
            else:
                # Update existing node to not_tested status
                node = response['nodes'][0]
                update_data = {"status": "not_tested"}
                update_success, update_response = self.make_request('PUT', f'nodes/{node["id"]}', update_data)
                if update_success:
                    print(f"   ✅ Reset node {ip} to not_tested status")
        
        # Get the node IDs for our test IPs
        test_node_ids = []
        for ip in known_ips:
            success, response = self.make_request('GET', f'nodes?ip={ip}')
            if success and 'nodes' in response and response['nodes']:
                test_node_ids.append(response['nodes'][0]['id'])
        
        if not test_node_ids:
            self.log_test("Complete Workflow - Setup Test Nodes", False, "No test nodes available")
            return False
        
        print(f"📋 Testing workflow with {len(test_node_ids)} known working IPs")
        
        # Step 1: Manual Ping Test (not_tested → ping_ok)
        print(f"\n🏓 STEP 1: Manual Ping Test")
        ping_data = {"node_ids": test_node_ids}
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
        
        if not ping_success or 'results' not in ping_response:
            self.log_test("Complete Workflow - Step 1 Ping", False, f"Ping test failed: {ping_response}")
            return False
        
        ping_ok_nodes = []
        for result in ping_response['results']:
            print(f"   Node {result['node_id']}: {result.get('message', 'No message')}")
            if result.get('success') and result.get('status') == 'ping_ok':
                ping_ok_nodes.append(result['node_id'])
        
        print(f"   ✅ Ping OK: {len(ping_ok_nodes)} nodes")
        
        if not ping_ok_nodes:
            self.log_test("Complete Workflow - Step 1 Ping", False, "No nodes passed ping test")
            return False
        
        # Step 2: Manual Speed Test (ping_ok → speed_ok)
        print(f"\n🚀 STEP 2: Manual Speed Test")
        speed_data = {"node_ids": ping_ok_nodes}
        speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
        
        if not speed_success or 'results' not in speed_response:
            self.log_test("Complete Workflow - Step 2 Speed", False, f"Speed test failed: {speed_response}")
            return False
        
        speed_ok_nodes = []
        for result in speed_response['results']:
            print(f"   Node {result['node_id']}: {result.get('message', 'No message')} (Speed: {result.get('speed', 'N/A')})")
            if result.get('success') and result.get('status') == 'speed_ok':
                speed_ok_nodes.append(result['node_id'])
        
        print(f"   ✅ Speed OK: {len(speed_ok_nodes)} nodes")
        
        if not speed_ok_nodes:
            self.log_test("Complete Workflow - Step 2 Speed", False, "No nodes passed speed test")
            return False
        
        # Step 3: Manual Launch Services (speed_ok → online)
        print(f"\n🚀 STEP 3: Manual Launch Services")
        launch_data = {"node_ids": speed_ok_nodes}
        launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
        
        if not launch_success or 'results' not in launch_response:
            self.log_test("Complete Workflow - Step 3 Launch", False, f"Service launch failed: {launch_response}")
            return False
        
        online_nodes = []
        socks_generated = []
        ovpn_generated = []
        
        for result in launch_response['results']:
            print(f"   Node {result['node_id']}: {result.get('message', 'No message')}")
            if result.get('success') and result.get('status') == 'online':
                online_nodes.append(result['node_id'])
                
                # Check SOCKS credentials
                if 'socks' in result and result['socks']:
                    socks = result['socks']
                    print(f"      SOCKS: {socks.get('ip')}:{socks.get('port')} ({socks.get('login')}/{socks.get('password')})")
                    socks_generated.append(result['node_id'])
                
                # Check OVPN config
                if 'ovpn_config' in result and result['ovpn_config']:
                    print(f"      OVPN: {len(result['ovpn_config'])} characters")
                    ovpn_generated.append(result['node_id'])
        
        print(f"   ✅ Online: {len(online_nodes)} nodes")
        print(f"   ✅ SOCKS generated: {len(socks_generated)} nodes")
        print(f"   ✅ OVPN generated: {len(ovpn_generated)} nodes")
        
        if online_nodes:
            self.log_test("Complete Workflow with Known IPs", True, 
                         f"Successfully completed workflow: {len(test_node_ids)} → {len(ping_ok_nodes)} → {len(speed_ok_nodes)} → {len(online_nodes)}")
            return True
        else:
            self.log_test("Complete Workflow with Known IPs", False, "No nodes reached online status")
            return False

    def test_error_handling(self):
        """Test error handling: speed test on ping_failed node should be rejected"""
        print("\n🚨 TESTING ERROR HANDLING")
        print("=" * 60)
        
        # Get a ping_failed node
        success, response = self.make_request('GET', 'nodes?status=ping_failed&limit=1')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Error Handling - Get ping_failed node", False, "No ping_failed nodes available")
            return False
        
        node_id = response['nodes'][0]['id']
        print(f"📋 Testing error handling with ping_failed Node {node_id}")
        
        # Try to run speed test on ping_failed node (should be rejected)
        speed_data = {"node_ids": [node_id]}
        speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
        
        if speed_success and 'results' in speed_response and speed_response['results']:
            result = speed_response['results'][0]
            
            # Should fail with appropriate error message
            if not result.get('success') and 'ping_ok' in result.get('message', '').lower():
                self.log_test("Error Handling - Speed test on ping_failed", True, 
                             f"Correctly rejected ping_failed node")
                return True
            else:
                self.log_test("Error Handling - Speed test on ping_failed", False, 
                             f"Should reject ping_failed node: {result}")
                return False
        else:
            self.log_test("Error Handling - Speed test on ping_failed", False, 
                         f"Speed test failed: {speed_response}")
            return False

    def test_database_verification(self):
        """Verify database updates and SOCKS/OVPN data storage"""
        print("\n💾 TESTING DATABASE VERIFICATION")
        print("=" * 60)
        
        # Get online nodes to verify database storage
        success, response = self.make_request('GET', 'nodes?status=online&limit=3')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Database Verification - Get online nodes", False, "No online nodes available")
            return False
        
        online_nodes = response['nodes']
        verified_count = 0
        
        for node in online_nodes:
            # Check SOCKS fields
            socks_fields = ['socks_ip', 'socks_port', 'socks_login', 'socks_password']
            socks_complete = all(node.get(field) is not None for field in socks_fields)
            
            # Check OVPN config
            ovpn_complete = node.get('ovpn_config') is not None and len(node.get('ovpn_config', '')) > 0
            
            if socks_complete and ovpn_complete:
                verified_count += 1
                print(f"   ✅ Node {node['id']}: SOCKS and OVPN data complete")
            else:
                print(f"   ❌ Node {node['id']}: Missing SOCKS ({socks_complete}) or OVPN ({ovpn_complete})")
        
        if verified_count > 0:
            self.log_test("Database Verification", True, 
                         f"{verified_count}/{len(online_nodes)} nodes have complete data")
            return True
        else:
            self.log_test("Database Verification", False, "No nodes have complete SOCKS/OVPN data")
            return False

    def run_workflow_tests(self):
        """Run the complete workflow tests as requested in review"""
        print("🔥 CRITICAL WORKFLOW TESTING (Review Request)")
        print("=" * 80)
        
        # Authentication
        if not self.test_login():
            print("❌ Login failed - cannot continue tests")
            return False
        
        # Test 1: Complete workflow with known working IPs
        self.test_complete_workflow_with_known_ips()
        
        # Test 2: Error handling
        self.test_error_handling()
        
        # Test 3: Database verification
        self.test_database_verification()
        
        # Summary
        print("\n" + "=" * 80)
        print("🏁 WORKFLOW TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL WORKFLOW TESTS PASSED!")
            return True
        else:
            print("❌ SOME WORKFLOW TESTS FAILED")
            return False

def main():
    tester = WorkflowTester()
    success = tester.run_workflow_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())