#!/usr/bin/env python3

import requests
import time
import sys
import subprocess

class IsolatedSpeedOKTester:
    def __init__(self):
        self.base_url = "https://memory-mcp.preview.emergentagent.com/api"
        self.token = None
        self.test_results = []
        self.tests_passed = 0
        self.tests_run = 0

    def log_test(self, test_name, success, message):
        """Log test result"""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")

    def make_request(self, method, endpoint, data=None):
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                return True, response.json()
            else:
                return False, {'error': f'HTTP {response.status_code}', 'message': response.text}
        except Exception as e:
            return False, {'error': str(e)}

    def test_login(self):
        """Test login functionality"""
        print("\n🔐 Testing Login")
        
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log_test("Login", True, "Successfully authenticated")
            return True
        else:
            self.log_test("Login", False, f"Login failed: {response}")
            return False

    def test_speed_ok_status_preservation_isolated(self):
        """ISOLATED SPEED_OK STATUS TESTING - Background Monitoring Disabled (Review Request)"""
        print("\n🔥 ISOLATED SPEED_OK STATUS PRESERVATION TESTING")
        print("🚫 Background monitoring has been TEMPORARILY DISABLED")
        print("=" * 80)
        
        # Test 1: Create speed_ok nodes with background monitoring disabled
        print("\n📋 TEST 1: Create speed_ok nodes with background monitoring disabled")
        
        node1_data = {
            "ip": "201.1.1.1",
            "login": "speedtest1",
            "password": "test123",
            "status": "speed_ok",
            "provider": "Test Provider",
            "comment": "Test node for speed_ok preservation"
        }
        
        success1, response1 = self.make_request('POST', 'nodes', node1_data)
        
        if not success1 or 'id' not in response1:
            self.log_test("Speed_OK Preservation - Create Node 1", False, f"Failed to create node: {response1}")
            return False
        
        node1_id = response1['id']
        print(f"✅ Node 1 created: ID={node1_id}, IP=201.1.1.1")
        
        # Wait 2 seconds
        time.sleep(2)
        
        # Verify node 1 status immediately by getting all nodes and finding our node
        success_check1, response_check1 = self.make_request('GET', 'nodes')
        node1_status = 'unknown'
        
        if success_check1 and 'nodes' in response_check1:
            for node in response_check1['nodes']:
                if node.get('id') == node1_id:
                    node1_status = node.get('status', 'unknown')
                    break
        
        print(f"🔍 Node 1 status from nodes list: {node1_status}")
        
        if node1_status == 'speed_ok':
            print(f"✅ Node 1 status immediately after creation: speed_ok")
            self.log_test("Speed_OK Preservation - Immediate Status Check", True, "Node has speed_ok status immediately after creation")
        else:
            print(f"❌ Node 1 status immediately after creation: {node1_status}")
            self.log_test("Speed_OK Preservation - Immediate Status Check", False, f"Expected speed_ok, got {node1_status}")
            return False
        
        # Test 2: Verify status persists for 30 seconds
        print("\n⏰ TEST 2: Verify status persists for 30 seconds")
        
        # Wait 15 seconds
        print("⏳ Waiting 15 seconds...")
        time.sleep(15)
        
        success_check2, response_check2 = self.make_request('GET', 'nodes')
        status_15s = 'unknown'
        if success_check2 and 'nodes' in response_check2:
            for node in response_check2['nodes']:
                if node.get('id') == node1_id:
                    status_15s = node.get('status', 'unknown')
                    break
        print(f"📊 After 15 seconds: {status_15s}")
        
        # Wait another 15 seconds
        print("⏳ Waiting another 15 seconds...")
        time.sleep(15)
        
        success_check3, response_check3 = self.make_request('GET', 'nodes')
        status_30s = 'unknown'
        if success_check3 and 'nodes' in response_check3:
            for node in response_check3['nodes']:
                if node.get('id') == node1_id:
                    status_30s = node.get('status', 'unknown')
                    break
        print(f"📊 After 30 seconds total: {status_30s}")
        
        if status_15s == 'speed_ok' and status_30s == 'speed_ok':
            self.log_test("Speed_OK Preservation - 30 Second Persistence", True, "Node maintained speed_ok status for 30+ seconds")
        else:
            self.log_test("Speed_OK Preservation - 30 Second Persistence", False, f"Status changed: 15s={status_15s}, 30s={status_30s}")
            return False
        
        # Test 3: Create multiple speed_ok nodes
        print("\n📋 TEST 3: Create multiple speed_ok nodes")
        
        additional_nodes = []
        for i in range(2, 5):  # Create nodes 2, 3, 4
            node_data = {
                "ip": f"201.1.1.{i}",
                "login": f"speedtest{i}",
                "password": "test123",
                "status": "speed_ok"
            }
            
            success, response = self.make_request('POST', 'nodes', node_data)
            if success and 'id' in response:
                additional_nodes.append(response['id'])
                print(f"✅ Node {i} created: ID={response['id']}, IP=201.1.1.{i}")
            else:
                print(f"❌ Failed to create node {i}: {response}")
            
            time.sleep(1)
        
        # Query all speed_ok nodes
        success_query, response_query = self.make_request('GET', 'nodes?status=speed_ok')
        if success_query and 'nodes' in response_query:
            speed_ok_count = len(response_query['nodes'])
            print(f"📊 Total speed_ok nodes found: {speed_ok_count}")
            
            if speed_ok_count >= 4:
                self.log_test("Speed_OK Preservation - Multiple Nodes", True, f"Successfully created {speed_ok_count} speed_ok nodes")
            else:
                self.log_test("Speed_OK Preservation - Multiple Nodes", False, f"Expected 4+ speed_ok nodes, found {speed_ok_count}")
        else:
            self.log_test("Speed_OK Preservation - Multiple Nodes", False, f"Failed to query speed_ok nodes: {response_query}")
        
        # Test 4: Check backend logs for node creation
        print("\n📋 TEST 4: Check backend logs for node creation")
        try:
            result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                                  capture_output=True, text=True, timeout=10)
            
            log_content = result.stdout
            speed_ok_mentions = log_content.count('speed_ok')
            node_creation_mentions = log_content.count('Creating node') + log_content.count('Node object status')
            
            print(f"📊 Backend log analysis:")
            print(f"   - speed_ok mentions: {speed_ok_mentions}")
            print(f"   - Node creation mentions: {node_creation_mentions}")
            
            if speed_ok_mentions > 0:
                self.log_test("Speed_OK Preservation - Backend Logs", True, f"Found {speed_ok_mentions} speed_ok mentions in logs")
            else:
                self.log_test("Speed_OK Preservation - Backend Logs", False, "No speed_ok mentions found in backend logs")
        except Exception as e:
            self.log_test("Speed_OK Preservation - Backend Logs", False, f"Failed to check logs: {e}")
        
        # Test 5: Test manual_ping_test skipping behavior
        print("\n📋 TEST 5: Test manual_ping_test skipping behavior")
        
        ping_test_data = {"node_ids": [node1_id]}
        success_ping, response_ping = self.make_request('POST', 'manual/ping-test', ping_test_data)
        
        if success_ping and 'results' in response_ping:
            result = response_ping['results'][0] if response_ping['results'] else {}
            message = result.get('message', '')
            
            if 'speed_ok status - test skipped' in message or 'SKIPPING' in message:
                print(f"✅ Manual ping test correctly skipped: {message}")
                self.log_test("Speed_OK Preservation - Ping Test Skipping", True, "Manual ping test correctly skipped speed_ok node")
            else:
                print(f"❌ Manual ping test did not skip: {message}")
                self.log_test("Speed_OK Preservation - Ping Test Skipping", False, f"Expected skip message, got: {message}")
        else:
            self.log_test("Speed_OK Preservation - Ping Test Skipping", False, f"Manual ping test failed: {response_ping}")
        
        # Verify node still has speed_ok status after ping test attempt
        success_final, response_final = self.make_request('GET', 'nodes')
        final_status = 'unknown'
        if success_final and 'nodes' in response_final:
            for node in response_final['nodes']:
                if node.get('id') == node1_id:
                    final_status = node.get('status', 'unknown')
                    break
        
        if final_status == 'speed_ok':
            print(f"✅ Node still has speed_ok status after ping test: {final_status}")
        else:
            print(f"❌ Node status changed after ping test: {final_status}")
            self.log_test("Speed_OK Preservation - Status After Ping Test", False, f"Status changed to {final_status}")
            return False
        
        # Test 6: Test service operations
        print("\n📋 TEST 6: Test service operations")
        
        service_start_data = {
            "node_ids": [node1_id],
            "action": "start"
        }
        
        success_service, response_service = self.make_request('POST', 'services/start', service_start_data)
        
        if success_service and 'results' in response_service:
            result = response_service['results'][0] if response_service['results'] else {}
            print(f"📊 Service start result: {result.get('message', 'No message')}")
            
            # Wait 2 seconds for any status changes
            time.sleep(2)
            
            # Verify status after service operation
            success_service_check, response_service_check = self.make_request('GET', 'nodes')
            service_status = 'unknown'
            if success_service_check and 'nodes' in response_service_check:
                for node in response_service_check['nodes']:
                    if node.get('id') == node1_id:
                        service_status = node.get('status', 'unknown')
                        break
            
            if service_status in ['speed_ok', 'online']:
                print(f"✅ Node maintained good status after service operation: {service_status}")
                self.log_test("Speed_OK Preservation - Service Operations", True, f"Node status preserved or improved: {service_status}")
            else:
                print(f"❌ Node status degraded after service operation: {service_status}")
                self.log_test("Speed_OK Preservation - Service Operations", False, f"Status degraded to {service_status}")
        else:
            self.log_test("Speed_OK Preservation - Service Operations", False, f"Service start failed: {response_service}")
        
        # Final Summary
        print("\n" + "=" * 80)
        print("🏁 SPEED_OK STATUS PRESERVATION TEST SUMMARY")
        
        # Count passed tests
        speed_ok_tests = [test for test in self.test_results if 'Speed_OK Preservation' in test['test']]
        passed_speed_ok_tests = [test for test in speed_ok_tests if test['success']]
        
        print(f"📊 Speed_OK Tests: {len(passed_speed_ok_tests)}/{len(speed_ok_tests)} passed")
        
        if len(passed_speed_ok_tests) == len(speed_ok_tests):
            print("🎉 ALL SPEED_OK PRESERVATION TESTS PASSED!")
            print("✅ Background monitoring was the sole cause of speed_ok nodes changing to ping_failed")
            return True
        else:
            print("⚠️ SOME SPEED_OK PRESERVATION TESTS FAILED")
            print("❌ There are other processes interfering with speed_ok status")
            return False

    def run_isolated_test(self):
        """Run ONLY the isolated speed_ok status preservation test"""
        print(f"\n🚀 Starting ISOLATED SPEED_OK STATUS TESTING")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Authentication first
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Run the isolated speed_ok test
        result = self.test_speed_ok_status_preservation_isolated()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"🏁 Isolated Speed_OK Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📊 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return result

if __name__ == "__main__":
    tester = IsolatedSpeedOKTester()
    success = tester.run_isolated_test()
    sys.exit(0 if success else 1)