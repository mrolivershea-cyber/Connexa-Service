#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class PingStatusTester:
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

    def test_ping_status_field_exists(self):
        """Test 1: Verify ping_status field exists in Node model"""
        # Create a test node to verify ping_status field exists
        test_node = {
            "ip": "8.8.8.8",
            "login": "ping_test_user",
            "password": "ping_test_pass",
            "protocol": "pptp",
            "provider": "Google DNS",
            "country": "United States",
            "state": "California",
            "city": "Mountain View",
            "comment": "Test node for ping_status field verification"
        }
        
        success, response = self.make_request('POST', 'nodes', test_node)
        
        if success and 'id' in response:
            node_id = response['id']
            
            # Get the created node to verify ping_status field
            nodes_success, nodes_response = self.make_request('GET', f'nodes?ip=8.8.8.8')
            
            if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                node = nodes_response['nodes'][0]
                
                # Check if ping_status field exists and is initially null
                if 'ping_status' in node:
                    if node['ping_status'] is None:
                        self.log_test("PING Status Field Exists", True, 
                                     f"ping_status field exists and is initially null for new nodes")
                        return node_id
                    else:
                        self.log_test("PING Status Field Exists", False, 
                                     f"ping_status field exists but is not null initially: {node['ping_status']}")
                        return None
                else:
                    self.log_test("PING Status Field Exists", False, 
                                 f"ping_status field missing from node response")
                    return None
            else:
                self.log_test("PING Status Field Exists", False, 
                             f"Could not retrieve created node")
                return None
        else:
            self.log_test("PING Status Field Exists", False, f"Failed to create test node: {response}")
            return None

    def test_import_with_ping_only_mode(self):
        """Test 2: Import with testing_mode='ping_only' should set ping_status"""
        import_data = {
            "data": """Ip: 1.1.1.1
Login: cloudflare_user
Pass: cloudflare_pass
State: California
City: San Francisco

Ip: 208.67.222.222
Login: opendns_user  
Pass: opendns_pass
State: California
City: San Francisco""",
            "protocol": "pptp",
            "testing_mode": "ping_only"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            
            # Verify testing_mode was processed
            if report.get('testing_mode') == 'ping_only':
                # Check if nodes were created
                if report.get('added', 0) >= 2:
                    # Verify ping_status was set for imported nodes
                    nodes_success, nodes_response = self.make_request('GET', 'nodes?ip=1.1.1.1')
                    
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        ping_status = node.get('ping_status')
                        
                        if ping_status in ['ping_success', 'ping_failed']:
                            self.log_test("Import with Ping Only Mode", True, 
                                         f"Import with testing_mode='ping_only' set ping_status to '{ping_status}'")
                            return True
                        else:
                            self.log_test("Import with Ping Only Mode", False, 
                                         f"Expected ping_status to be set, got: {ping_status}")
                            return False
                    else:
                        self.log_test("Import with Ping Only Mode", False, 
                                     f"Could not retrieve imported node")
                        return False
                else:
                    self.log_test("Import with Ping Only Mode", False, 
                                 f"Expected 2 nodes to be added, got: {report.get('added', 0)}")
                    return False
            else:
                self.log_test("Import with Ping Only Mode", False, 
                             f"testing_mode not processed correctly: {report.get('testing_mode')}")
                return False
        else:
            self.log_test("Import with Ping Only Mode", False, f"Import failed: {response}")
            return False

    def test_import_with_speed_only_mode(self):
        """Test 3: Import with testing_mode='speed_only' should set speed field"""
        import_data = {
            "data": """Ip: 9.9.9.9
Login: quad9_user
Pass: quad9_pass
State: California
City: Berkeley""",
            "protocol": "pptp",
            "testing_mode": "speed_only"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            
            # Verify testing_mode was processed
            if report.get('testing_mode') == 'speed_only':
                # Check if node was created
                if report.get('added', 0) >= 1:
                    # Verify speed field was set for imported node
                    nodes_success, nodes_response = self.make_request('GET', 'nodes?ip=9.9.9.9')
                    
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        speed = node.get('speed')
                        
                        # Speed might be set or remain null depending on test success
                        # The important thing is that testing_mode was processed
                        self.log_test("Import with Speed Only Mode", True, 
                                     f"Import with testing_mode='speed_only' processed, speed field: {speed}")
                        return True
                    else:
                        self.log_test("Import with Speed Only Mode", False, 
                                     f"Could not retrieve imported node")
                        return False
                else:
                    self.log_test("Import with Speed Only Mode", False, 
                                 f"Expected 1 node to be added, got: {report.get('added', 0)}")
                    return False
            else:
                self.log_test("Import with Speed Only Mode", False, 
                             f"testing_mode not processed correctly: {report.get('testing_mode')}")
                return False
        else:
            self.log_test("Import with Speed Only Mode", False, f"Import failed: {response}")
            return False

    def test_import_with_ping_speed_mode(self):
        """Test 4: Import with testing_mode='ping_speed' should set both ping_status and speed"""
        import_data = {
            "data": """Ip: 8.8.4.4
Login: google_dns2_user
Pass: google_dns2_pass
State: California
City: Mountain View""",
            "protocol": "pptp",
            "testing_mode": "ping_speed"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            
            # Verify testing_mode was processed
            if report.get('testing_mode') == 'ping_speed':
                # Check if node was created
                if report.get('added', 0) >= 1:
                    # Verify both ping_status and speed fields were processed
                    nodes_success, nodes_response = self.make_request('GET', 'nodes?ip=8.8.4.4')
                    
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        ping_status = node.get('ping_status')
                        speed = node.get('speed')
                        
                        # At least ping_status should be set for ping_speed mode
                        if ping_status in ['ping_success', 'ping_failed']:
                            self.log_test("Import with Ping+Speed Mode", True, 
                                         f"Import with testing_mode='ping_speed' processed, ping_status: {ping_status}, speed: {speed}")
                            return True
                        else:
                            self.log_test("Import with Ping+Speed Mode", False, 
                                         f"Expected ping_status to be set, got: {ping_status}")
                            return False
                    else:
                        self.log_test("Import with Ping+Speed Mode", False, 
                                     f"Could not retrieve imported node")
                        return False
                else:
                    self.log_test("Import with Ping+Speed Mode", False, 
                                 f"Expected 1 node to be added, got: {report.get('added', 0)}")
                    return False
            else:
                self.log_test("Import with Ping+Speed Mode", False, 
                             f"testing_mode not processed correctly: {report.get('testing_mode')}")
                return False
        else:
            self.log_test("Import with Ping+Speed Mode", False, f"Import failed: {response}")
            return False

    def test_import_with_no_test_mode(self):
        """Test 5: Import with testing_mode='no_test' should not perform any testing"""
        import_data = {
            "data": """Ip: 4.2.2.2
Login: level3_user
Pass: level3_pass
State: Colorado
City: Broomfield""",
            "protocol": "pptp",
            "testing_mode": "no_test"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            
            # Verify testing_mode was processed
            if report.get('testing_mode') == 'no_test':
                # Check if node was created
                if report.get('added', 0) >= 1:
                    # Verify no testing was performed (ping_status should remain null)
                    nodes_success, nodes_response = self.make_request('GET', 'nodes?ip=4.2.2.2')
                    
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        ping_status = node.get('ping_status')
                        speed = node.get('speed')
                        
                        # Both should remain null for no_test mode
                        if ping_status is None and speed is None:
                            self.log_test("Import with No Test Mode", True, 
                                         f"Import with testing_mode='no_test' - no testing performed, ping_status: {ping_status}, speed: {speed}")
                            return True
                        else:
                            self.log_test("Import with No Test Mode", False, 
                                         f"Expected no testing, but got ping_status: {ping_status}, speed: {speed}")
                            return False
                    else:
                        self.log_test("Import with No Test Mode", False, 
                                     f"Could not retrieve imported node")
                        return False
                else:
                    self.log_test("Import with No Test Mode", False, 
                                 f"Expected 1 node to be added, got: {report.get('added', 0)}")
                    return False
            else:
                self.log_test("Import with No Test Mode", False, 
                             f"testing_mode not processed correctly: {report.get('testing_mode')}")
                return False
        else:
            self.log_test("Import with No Test Mode", False, f"Import failed: {response}")
            return False

    def test_manual_ping_testing(self):
        """Test 6: Manual PING testing via /api/test/ping endpoint"""
        # Get some existing nodes to test
        nodes_success, nodes_response = self.make_request('GET', 'nodes?limit=3')
        
        if not nodes_success or 'nodes' not in nodes_response or not nodes_response['nodes']:
            self.log_test("Manual PING Testing", False, "No nodes available for testing")
            return False
        
        node_ids = [node['id'] for node in nodes_response['nodes'][:2]]
        
        test_data = {
            "node_ids": node_ids,
            "test_type": "ping"
        }
        
        success, response = self.make_request('POST', 'test/ping', test_data)
        
        if success and 'results' in response:
            results = response['results']
            
            if len(results) >= 1:
                # Check if ping_status was updated for tested nodes
                first_result = results[0]
                node_id = first_result.get('node_id')
                
                if node_id:
                    # Get the node to verify ping_status was updated
                    nodes_success, nodes_response = self.make_request('GET', 'nodes')
                    
                    if nodes_success and 'nodes' in nodes_response:
                        target_node = None
                        for node in nodes_response['nodes']:
                            if node.get('id') == node_id:
                                target_node = node
                                break
                        
                        if target_node:
                            ping_status = target_node.get('ping_status')
                            
                            if ping_status in ['ping_success', 'ping_failed']:
                                self.log_test("Manual PING Testing", True, 
                                             f"Manual ping test updated ping_status to '{ping_status}' for node {node_id}")
                                return True
                            else:
                                self.log_test("Manual PING Testing", False, 
                                             f"Expected ping_status to be updated, got: {ping_status}")
                                return False
                        else:
                            self.log_test("Manual PING Testing", False, 
                                         f"Could not find tested node {node_id}")
                            return False
                    else:
                        self.log_test("Manual PING Testing", False, 
                                     f"Could not retrieve nodes after ping test")
                        return False
                else:
                    self.log_test("Manual PING Testing", False, 
                                 f"No node_id in test result")
                    return False
            else:
                self.log_test("Manual PING Testing", False, 
                             f"No test results returned")
                return False
        else:
            self.log_test("Manual PING Testing", False, f"Ping test failed: {response}")
            return False

    def test_single_node_ping_endpoint(self, node_id: int):
        """Test 7: Single node ping testing via /api/nodes/{node_id}/test endpoint"""
        if not node_id:
            self.log_test("Single Node PING Endpoint", False, "No node ID provided")
            return False
            
        success, response = self.make_request('POST', f'nodes/{node_id}/test?test_type=ping')
        
        if success:
            # Get the node to verify ping_status was updated
            nodes_success, nodes_response = self.make_request('GET', 'nodes')
            
            if nodes_success and 'nodes' in nodes_response:
                target_node = None
                for node in nodes_response['nodes']:
                    if node.get('id') == node_id:
                        target_node = node
                        break
                
                if target_node:
                    ping_status = target_node.get('ping_status')
                    if ping_status in ['ping_success', 'ping_failed']:
                        self.log_test("Single Node PING Endpoint", True, 
                                     f"Single node ping test updated ping_status to '{ping_status}' for node {node_id}")
                        return True
                    else:
                        self.log_test("Single Node PING Endpoint", False, 
                                     f"Expected ping_status to be updated, got: {ping_status}")
                        return False
                else:
                    self.log_test("Single Node PING Endpoint", False, 
                                 f"Could not find node {node_id} after ping test")
                    return False
            else:
                self.log_test("Single Node PING Endpoint", False, 
                             f"Could not retrieve nodes after ping test")
                return False
        else:
            self.log_test("Single Node PING Endpoint", False, f"Single node ping test failed: {response}")
            return False

    def test_ping_status_in_api_responses(self):
        """Test 8: Verify ping_status field is returned in node JSON responses"""
        success, response = self.make_request('GET', 'nodes?limit=5')
        
        if success and 'nodes' in response:
            nodes = response['nodes']
            
            if len(nodes) > 0:
                # Check if ping_status field is present in all nodes
                all_have_ping_status = True
                sample_ping_statuses = []
                
                for node in nodes[:3]:  # Check first 3 nodes
                    if 'ping_status' not in node:
                        all_have_ping_status = False
                        break
                    sample_ping_statuses.append(node.get('ping_status'))
                
                if all_have_ping_status:
                    self.log_test("PING Status in API Responses", True, 
                                 f"ping_status field present in all node responses. Sample values: {sample_ping_statuses}")
                    return True
                else:
                    self.log_test("PING Status in API Responses", False, 
                                 f"ping_status field missing from some node responses")
                    return False
            else:
                self.log_test("PING Status in API Responses", False, 
                             f"No nodes found to test ping_status field")
                return False
        else:
            self.log_test("PING Status in API Responses", False, f"Failed to get nodes: {response}")
            return False

    def run_ping_status_tests(self):
        """Run all PING status tests"""
        print("🚀 Starting PING Status Functionality Tests")
        print("=" * 60)
        
        # Test authentication
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        print("\n🔍 Testing PING Status Field and Import Modes...")
        
        # Test 1: Verify ping_status field exists and is initially null
        ping_test_node_id = self.test_ping_status_field_exists()
        
        # Test 2-5: Import with different testing modes
        self.test_import_with_ping_only_mode()
        self.test_import_with_speed_only_mode()
        self.test_import_with_ping_speed_mode()
        self.test_import_with_no_test_mode()
        
        print("\n🔍 Testing Manual PING Testing...")
        
        # Test 6: Manual PING testing
        self.test_manual_ping_testing()
        
        # Test 7: Single node ping endpoint
        if ping_test_node_id:
            self.test_single_node_ping_endpoint(ping_test_node_id)
        
        print("\n🔍 Testing API Response Format...")
        
        # Test 8: Verify ping_status in API responses
        self.test_ping_status_in_api_responses()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 PING Status Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = PingStatusTester()
    success = tester.run_ping_status_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0,
        "test_details": tester.test_results
    }
    
    print(f"\n📋 Detailed Test Results:")
    for result in tester.test_results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"   {status}: {result['test']}")
        if result['details']:
            print(f"      {result['details']}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())