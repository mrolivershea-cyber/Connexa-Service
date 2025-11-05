#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class UnifiedStatusTester:
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

    def test_unified_status_stats_endpoint(self):
        """Test 1: GET /api/stats returns unified status counts"""
        success, response = self.make_request('GET', 'stats')
        
        if success and 'total' in response:
            # Check for unified status fields
            required_fields = ['not_tested', 'ping_failed', 'ping_ok', 'speed_slow', 'speed_ok', 'offline', 'online']
            missing_fields = []
            
            for field in required_fields:
                if field not in response:
                    missing_fields.append(field)
            
            if not missing_fields:
                self.log_test("Unified Status Stats Endpoint", True, 
                             f"✅ All unified status counts present: not_tested={response.get('not_tested', 0)}, ping_failed={response.get('ping_failed', 0)}, ping_ok={response.get('ping_ok', 0)}, speed_slow={response.get('speed_slow', 0)}, speed_ok={response.get('speed_ok', 0)}, offline={response.get('offline', 0)}, online={response.get('online', 0)}")
                return True
            else:
                self.log_test("Unified Status Stats Endpoint", False, 
                             f"❌ Missing unified status fields: {missing_fields}")
                return False
        else:
            self.log_test("Unified Status Stats Endpoint", False, f"Failed to get stats: {response}")
            return False

    def test_unified_status_ping_test_endpoint(self):
        """Test 2: POST /api/test/ping sets unified status (ping_ok/ping_failed)"""
        # First create a test node
        test_node = {
            "ip": "8.8.8.8",
            "login": "unified_test_user",
            "password": "unified_test_pass",
            "protocol": "pptp",
            "status": "not_tested"  # Start with not_tested
        }
        
        success, response = self.make_request('POST', 'nodes', test_node)
        
        if success and 'id' in response:
            node_id = response['id']
            
            # Test ping endpoint
            test_data = {
                "node_ids": [node_id],
                "test_type": "ping"
            }
            
            ping_success, ping_response = self.make_request('POST', 'test/ping', test_data)
            
            if ping_success and 'results' in ping_response:
                # Check if node status was updated to ping_ok or ping_failed
                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip=8.8.8.8')
                
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    status = node.get('status')
                    
                    if status in ['ping_ok', 'ping_failed']:
                        self.log_test("Unified Status Ping Test Endpoint", True, 
                                     f"✅ Ping test set unified status to '{status}'")
                        return node_id
                    else:
                        self.log_test("Unified Status Ping Test Endpoint", False, 
                                     f"❌ Expected status 'ping_ok' or 'ping_failed', got '{status}'")
                        return None
                else:
                    self.log_test("Unified Status Ping Test Endpoint", False, 
                                 f"❌ Could not retrieve node after ping test")
                    return None
            else:
                self.log_test("Unified Status Ping Test Endpoint", False, 
                             f"❌ Ping test failed: {ping_response}")
                return None
        else:
            self.log_test("Unified Status Ping Test Endpoint", False, 
                         f"❌ Failed to create test node: {response}")
            return None

    def test_unified_status_speed_test_requires_ping_ok(self):
        """Test 3: Speed test only works when status is ping_ok or better"""
        # Create a node with ping_failed status
        test_node = {
            "ip": "192.0.2.1",  # RFC5737 test IP
            "login": "speed_test_user",
            "password": "speed_test_pass",
            "protocol": "pptp",
            "status": "ping_failed"
        }
        
        success, response = self.make_request('POST', 'nodes', test_node)
        
        if success and 'id' in response:
            node_id = response['id']
            
            # Try speed test on ping_failed node (should fail or be rejected)
            test_data = {
                "node_ids": [node_id],
                "test_type": "speed"
            }
            
            speed_success, speed_response = self.make_request('POST', 'test/speed', test_data)
            
            # Check if speed test was properly rejected or handled
            if speed_success and 'results' in speed_response:
                results = speed_response['results']
                if results and len(results) > 0:
                    result = results[0]
                    # Speed test should fail or indicate service not active
                    if not result.get('success', True) or 'not active' in result.get('message', '').lower():
                        self.log_test("Unified Status Speed Test Requires Ping OK", True, 
                                     f"✅ Speed test correctly rejected for ping_failed node: {result.get('message', 'Service not active')}")
                        return True
                    else:
                        self.log_test("Unified Status Speed Test Requires Ping OK", False, 
                                     f"❌ Speed test should not succeed on ping_failed node: {result}")
                        return False
                else:
                    self.log_test("Unified Status Speed Test Requires Ping OK", False, 
                                 f"❌ No results returned from speed test")
                    return False
            else:
                self.log_test("Unified Status Speed Test Requires Ping OK", False, 
                             f"❌ Speed test endpoint failed: {speed_response}")
                return False
        else:
            self.log_test("Unified Status Speed Test Requires Ping OK", False, 
                         f"❌ Failed to create test node: {response}")
            return False

    def test_unified_status_service_start_sets_online_offline(self):
        """Test 4: Service start sets status to online/offline based on success"""
        # Create a node with ping_ok status
        test_node = {
            "ip": "203.0.113.10",  # RFC5737 test IP
            "login": "service_test_user",
            "password": "service_test_pass",
            "protocol": "pptp",
            "status": "ping_ok"
        }
        
        success, response = self.make_request('POST', 'nodes', test_node)
        
        if success and 'id' in response:
            node_id = response['id']
            
            # Try to start services
            service_data = {
                "node_ids": [node_id],
                "action": "start"
            }
            
            start_success, start_response = self.make_request('POST', 'services/start', service_data)
            
            if start_success and 'results' in start_response:
                # Check node status after service start attempt
                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip=203.0.113.10')
                
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    status = node.get('status')
                    
                    if status in ['online', 'offline']:
                        self.log_test("Unified Status Service Start Sets Online/Offline", True, 
                                     f"✅ Service start set unified status to '{status}' based on success/failure")
                        return True
                    else:
                        self.log_test("Unified Status Service Start Sets Online/Offline", False, 
                                     f"❌ Expected status 'online' or 'offline', got '{status}'")
                        return False
                else:
                    self.log_test("Unified Status Service Start Sets Online/Offline", False, 
                                 f"❌ Could not retrieve node after service start")
                    return False
            else:
                self.log_test("Unified Status Service Start Sets Online/Offline", False, 
                             f"❌ Service start failed: {start_response}")
                return False
        else:
            self.log_test("Unified Status Service Start Sets Online/Offline", False, 
                         f"❌ Failed to create test node: {response}")
            return False

    def test_unified_status_import_with_testing_sets_correct_status(self):
        """Test 5: Import with testing sets correct unified status based on test results"""
        import_data = {
            "data": """Ip: 1.1.1.1
Login: cloudflare_test
Pass: cloudflare_pass
State: California

Ip: 8.8.8.8
Login: google_test
Pass: google_pass
State: California""",
            "protocol": "pptp",
            "testing_mode": "ping_only"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            
            if report.get('added', 0) >= 2:
                # Check if imported nodes have correct unified status
                nodes_success, nodes_response = self.make_request('GET', 'nodes?ip=1.1.1.1')
                
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    status = node.get('status')
                    
                    # Should be ping_ok, ping_failed, or checking
                    if status in ['ping_ok', 'ping_failed', 'checking']:
                        self.log_test("Unified Status Import with Testing", True, 
                                     f"✅ Import with testing_mode='ping_only' set unified status to '{status}'")
                        return True
                    else:
                        self.log_test("Unified Status Import with Testing", False, 
                                     f"❌ Expected unified status (ping_ok/ping_failed/checking), got '{status}'")
                        return False
                else:
                    self.log_test("Unified Status Import with Testing", False, 
                                 f"❌ Could not retrieve imported node")
                    return False
            else:
                self.log_test("Unified Status Import with Testing", False, 
                             f"❌ No nodes were added during import: {report}")
                return False
        else:
            self.log_test("Unified Status Import with Testing", False, 
                         f"❌ Import failed: {response}")
            return False

    def test_unified_status_progression_logic(self):
        """Test 6: Verify unified status progression: not_tested → ping test → ping_ok/ping_failed → speed test → speed_ok/slow → service start → online/offline"""
        # Create a node with not_tested status
        test_node = {
            "ip": "198.51.100.1",  # RFC5737 test IP
            "login": "progression_test",
            "password": "progression_pass",
            "protocol": "pptp",
            "status": "not_tested"
        }
        
        success, response = self.make_request('POST', 'nodes', test_node)
        
        if success and 'id' in response:
            node_id = response['id']
            progression_steps = []
            
            # Step 1: Initial status should be not_tested
            nodes_success, nodes_response = self.make_request('GET', f'nodes?ip=198.51.100.1')
            if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                node = nodes_response['nodes'][0]
                initial_status = node.get('status')
                progression_steps.append(f"Initial: {initial_status}")
                
                # Step 2: Run ping test
                ping_data = {"node_ids": [node_id], "test_type": "ping"}
                ping_success, ping_response = self.make_request('POST', 'test/ping', ping_data)
                
                if ping_success:
                    # Check status after ping
                    nodes_success, nodes_response = self.make_request('GET', f'nodes?ip=198.51.100.1')
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        ping_status = node.get('status')
                        progression_steps.append(f"After ping: {ping_status}")
                        
                        # Step 3: If ping_ok, try speed test
                        if ping_status == 'ping_ok':
                            speed_data = {"node_ids": [node_id], "test_type": "speed"}
                            speed_success, speed_response = self.make_request('POST', 'test/speed', speed_data)
                            
                            if speed_success:
                                # Check status after speed test
                                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip=198.51.100.1')
                                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                                    node = nodes_response['nodes'][0]
                                    speed_status = node.get('status')
                                    progression_steps.append(f"After speed: {speed_status}")
                        
                        # Step 4: Try service start
                        service_data = {"node_ids": [node_id], "action": "start"}
                        service_success, service_response = self.make_request('POST', 'services/start', service_data)
                        
                        if service_success:
                            # Check final status
                            nodes_success, nodes_response = self.make_request('GET', f'nodes?ip=198.51.100.1')
                            if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                                node = nodes_response['nodes'][0]
                                final_status = node.get('status')
                                progression_steps.append(f"After service: {final_status}")
                
                # Verify logical progression
                progression_str = " → ".join(progression_steps)
                
                # Check if progression makes sense
                valid_progression = True
                if len(progression_steps) >= 2:
                    # Should progress from not_tested to something else
                    if 'not_tested' in progression_steps[0] and 'not_tested' not in progression_steps[-1]:
                        valid_progression = True
                    else:
                        valid_progression = False
                
                if valid_progression:
                    self.log_test("Unified Status Progression Logic", True, 
                                 f"✅ Status progression working: {progression_str}")
                    return True
                else:
                    self.log_test("Unified Status Progression Logic", False, 
                                 f"❌ Invalid status progression: {progression_str}")
                    return False
            else:
                self.log_test("Unified Status Progression Logic", False, 
                             f"❌ Could not retrieve test node")
                return False
        else:
            self.log_test("Unified Status Progression Logic", False, 
                         f"❌ Failed to create test node: {response}")
            return False

    def test_unified_status_no_ping_status_field_references(self):
        """Test 7: Verify no separate ping_status field references (should be unified in status)"""
        # Get a few nodes and check their structure
        success, response = self.make_request('GET', 'nodes?limit=5')
        
        if success and 'nodes' in response:
            nodes = response['nodes']
            
            if nodes:
                # Check first node structure
                node = nodes[0]
                
                # ping_status field should NOT exist (unified into status)
                if 'ping_status' not in node:
                    # status field should exist with unified values
                    status = node.get('status')
                    unified_statuses = ['not_tested', 'ping_failed', 'ping_ok', 'speed_slow', 'speed_ok', 'offline', 'online', 'checking']
                    
                    if status in unified_statuses:
                        self.log_test("Unified Status No Ping Status Field", True, 
                                     f"✅ No separate ping_status field found. Unified status: '{status}'")
                        return True
                    else:
                        self.log_test("Unified Status No Ping Status Field", False, 
                                     f"❌ Status field has non-unified value: '{status}'")
                        return False
                else:
                    self.log_test("Unified Status No Ping Status Field", False, 
                                 f"❌ Separate ping_status field still exists: {node.get('ping_status')}")
                    return False
            else:
                self.log_test("Unified Status No Ping Status Field", False, 
                             f"❌ No nodes found to test")
                return False
        else:
            self.log_test("Unified Status No Ping Status Field", False, 
                         f"❌ Failed to get nodes: {response}")
            return False

    def run_unified_status_tests(self):
        """Run all unified status system tests"""
        print(f"\n🔄 Starting Unified Status System Tests at {datetime.now()}")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 80)
        
        # Authentication tests
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # NEW UNIFIED STATUS SYSTEM TESTS (Priority)
        print("\n" + "="*50)
        print("🔄 UNIFIED STATUS SYSTEM TESTS (Review Request)")
        print("="*50)
        
        self.test_unified_status_stats_endpoint()
        ping_test_node_id = self.test_unified_status_ping_test_endpoint()
        self.test_unified_status_speed_test_requires_ping_ok()
        self.test_unified_status_service_start_sets_online_offline()
        self.test_unified_status_import_with_testing_sets_correct_status()
        self.test_unified_status_progression_logic()
        self.test_unified_status_no_ping_status_field_references()
        
        # Print summary
        print("\n" + "="*80)
        print(f"📊 UNIFIED STATUS TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL UNIFIED STATUS TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - check logs above")
        
        return self.tests_passed == self.tests_run

def main():
    tester = UnifiedStatusTester()
    success = tester.run_unified_status_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())