#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class PingWorkflowTester:
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

    def test_improved_ping_workflow(self):
        """Test the improved ping workflow as per review request"""
        print("\n🔥 TESTING IMPROVED PING WORKFLOW")
        print("=" * 60)
        
        # Get existing nodes from database, preferring working ones
        success, response = self.make_request('GET', 'nodes', {'limit': 20})
        
        if not success or 'nodes' not in response:
            self.log_test("Improved Ping Workflow - Setup", False, "Failed to get existing nodes")
            return False
        
        # Filter for nodes with different protocols and statuses
        all_nodes = response['nodes']
        working_nodes = [n for n in all_nodes if n.get('status') in ['speed_ok', 'ping_ok']]
        pptp_nodes = [n for n in all_nodes if n.get('protocol') == 'pptp']
        
        # Select test nodes: prefer working nodes but include some variety
        test_nodes = []
        if working_nodes:
            test_nodes.extend(working_nodes[:2])  # Use 2 working nodes
        if pptp_nodes and len(test_nodes) < 3:
            for node in pptp_nodes:
                if node not in test_nodes:
                    test_nodes.append(node)
                    if len(test_nodes) >= 3:
                        break
        
        # Fallback to any nodes if needed
        if len(test_nodes) < 3:
            for node in all_nodes:
                if node not in test_nodes:
                    test_nodes.append(node)
                    if len(test_nodes) >= 3:
                        break
        
        if len(test_nodes) < 3:
            self.log_test("Improved Ping Workflow - Setup", False, "Not enough nodes for testing")
            return False
        
        created_node_ids = [node['id'] for node in test_nodes]
        
        print(f"✅ Using existing nodes for testing:")
        for node in test_nodes:
            print(f"   - {node['ip']} (ID: {node['id']}, Protocol: {node.get('protocol', 'N/A')}, Status: {node.get('status', 'N/A')})")
        
        # Test 1: Single node ping test with mixed protocols
        print(f"\n📍 Test 1: Single node ping test")
        test1_success = self.test_single_node_ping_with_validation(created_node_ids[0])
        
        # Test 2: Batch ping test with progress tracking
        print(f"\n📍 Test 2: Batch ping test with progress")
        test2_success = self.test_batch_ping_with_progress(created_node_ids)
        
        # Test 3: Regression tests for speed test and launch services
        print(f"\n📍 Test 3: Regression tests")
        test3_success = self.test_regression_speed_and_launch(created_node_ids)
        
        # Test 4: Performance tests
        print(f"\n📍 Test 4: Performance tests")
        test4_success = self.test_ping_performance(created_node_ids)
        
        # Overall success
        success = test1_success and test2_success and test3_success and test4_success
        
        # No cleanup needed since we used existing nodes
        
        self.log_test("Improved Ping Workflow - Complete", success, 
                     "All ping workflow tests completed successfully" if success else "Some ping workflow tests failed")
        return success
    
    def test_single_node_ping_with_validation(self, node_id):
        """Test single node ping with field validation"""
        test_data = {"node_ids": [node_id]}
        
        start_time = time.time()
        success, response = self.make_request('POST', 'manual/ping-test', test_data)
        end_time = time.time()
        
        if success and 'results' in response:
            result = response['results'][0] if response['results'] else {}
            
            # Debug: Print the actual response (commented out for cleaner output)
            # print(f"   Debug - Ping result: {result}")
            
            # Validate required fields in ping_result
            ping_result = result.get('ping_result', {})
            required_fields = ['success', 'avg_time', 'success_rate', 'packet_loss']
            
            missing_fields = [field for field in required_fields if field not in ping_result]
            
            # Special case: if node has speed_ok status, ping test is skipped
            if result.get('status') == 'speed_ok' and 'message' in result and 'skipped' in result['message'].lower():
                self.log_test("Single Node Ping - Speed_OK Protection", True, 
                             f"Ping test correctly skipped for speed_ok node: {result.get('message')}")
                return True
            elif not missing_fields:
                self.log_test("Single Node Ping - Field Validation", True, 
                             f"All required fields present: {required_fields}")
                
                # Test response time (should be under 2 seconds)
                response_time = end_time - start_time
                if response_time < 2.0:
                    self.log_test("Single Node Ping - Performance", True, 
                                 f"Response time: {response_time:.2f}s (< 2s target)")
                    return True
                else:
                    self.log_test("Single Node Ping - Performance", False, 
                                 f"Response time: {response_time:.2f}s (> 2s target)")
                    return False
            else:
                self.log_test("Single Node Ping - Field Validation", False, 
                             f"Missing required fields: {missing_fields}")
                return False
        else:
            self.log_test("Single Node Ping - API Call", False, f"API call failed: {response}")
            return False
    
    def test_batch_ping_with_progress(self, node_ids):
        """Test batch ping with progress tracking"""
        test_data = {"node_ids": node_ids}
        
        # Test batch ping endpoint
        success, response = self.make_request('POST', 'manual/ping-test-batch-progress', test_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            
            # Test that API responds quickly with session_id
            self.log_test("Batch Ping - Quick Response", True, 
                         f"Got session_id: {session_id}")
            
            # Test progress endpoint
            time.sleep(1)  # Wait a bit for processing to start
            progress_success, progress_response = self.make_request('GET', f'progress/{session_id}')
            
            # Handle SSE response - look for progress data in the text
            if progress_success and 'text' in progress_response:
                sse_text = progress_response['text']
                if 'session_id' in sse_text and 'progress_percent' in sse_text:
                    self.log_test("Batch Ping - Progress Tracking", True, 
                                 f"SSE progress stream working - contains session_id and progress_percent")
                else:
                    self.log_test("Batch Ping - Progress Tracking", False, 
                                 f"SSE stream missing expected fields")
                    return False
            elif progress_success and 'session_id' in progress_response:
                self.log_test("Batch Ping - Progress Tracking", True, 
                             f"Progress: {progress_response.get('progress_percent', 0)}%")
                
                # Wait for completion and check no nodes left in 'checking'
                max_wait = 30  # 30 seconds max wait
                wait_time = 0
                
                while wait_time < max_wait:
                    time.sleep(2)
                    wait_time += 2
                    
                    progress_success, progress_response = self.make_request('GET', f'progress/{session_id}')
                    if progress_success and progress_response.get('status') in ['completed', 'failed']:
                        break
                
                # Check no nodes are stuck in 'checking' status
                return self.verify_no_checking_nodes(node_ids)
            else:
                self.log_test("Batch Ping - Progress Tracking", False, 
                             f"Progress endpoint failed: {progress_response}")
                return False
        else:
            self.log_test("Batch Ping - API Call", False, f"Batch ping failed: {response}")
            return False
    
    def verify_no_checking_nodes(self, node_ids):
        """Verify no nodes are left in 'checking' status"""
        checking_nodes = []
        
        for node_id in node_ids:
            success, response = self.make_request('GET', f'nodes/{node_id}')
            if success and response.get('status') == 'checking':
                checking_nodes.append(node_id)
        
        if not checking_nodes:
            self.log_test("Batch Ping - No Checking Nodes", True, 
                         "No nodes left in 'checking' status")
            return True
        else:
            self.log_test("Batch Ping - No Checking Nodes", False, 
                         f"Nodes stuck in 'checking': {checking_nodes}")
            return False
    
    def test_regression_speed_and_launch(self, node_ids):
        """Test regression for speed test and launch services"""
        # First set a node to ping_ok status for speed test
        node_id = node_ids[0]
        
        # Update node to ping_ok status
        update_data = {"status": "ping_ok"}
        success, response = self.make_request('PUT', f'nodes/{node_id}', update_data)
        
        if not success:
            self.log_test("Regression - Setup ping_ok", False, "Failed to set node to ping_ok")
            return False
        
        # Test speed test endpoint
        test_data = {"node_ids": [node_id]}
        success, response = self.make_request('POST', 'manual/speed-test', test_data)
        
        if success and 'results' in response:
            self.log_test("Regression - Speed Test", True, "Speed test endpoint working")
            
            # Set node to speed_ok for launch services test
            update_data = {"status": "speed_ok"}
            self.make_request('PUT', f'nodes/{node_id}', update_data)
            
            # Test launch services endpoint
            success, response = self.make_request('POST', 'manual/launch-services', test_data)
            
            if success and 'results' in response:
                result = response['results'][0] if response['results'] else {}
                
                # Verify speed_ok protection - node should remain speed_ok if service fails
                if result.get('status') == 'speed_ok' or result.get('status') == 'online':
                    self.log_test("Regression - Launch Services & Protection", True, 
                                 f"Service launch working, status preserved: {result.get('status')}")
                    return True
                else:
                    self.log_test("Regression - Launch Services & Protection", False, 
                                 f"Speed_ok protection failed, status: {result.get('status')}")
                    return False
            else:
                self.log_test("Regression - Launch Services", False, f"Launch services failed: {response}")
                return False
        else:
            self.log_test("Regression - Speed Test", False, f"Speed test failed: {response}")
            return False
    
    def test_ping_performance(self, node_ids):
        """Test ping performance requirements"""
        # Use only the first node for single performance test
        # Test single node performance (should be under 2 seconds)
        start_time = time.time()
        test_data = {"node_ids": [node_ids[0]]}
        success, response = self.make_request('POST', 'manual/ping-test', test_data)
        single_time = time.time() - start_time
        
        single_ok = single_time < 2.0
        self.log_test("Performance - Single Node", single_ok, 
                     f"Single node ping: {single_time:.2f}s ({'✅ < 2s' if single_ok else '❌ > 2s'})")
        
        # For batch test, use only first 2 nodes to avoid timeout issues
        # Test batch response time (should respond quickly with session_id)
        batch_nodes = node_ids[:2]  # Use only first 2 nodes
        
        start_time = time.time()
        test_data = {"node_ids": batch_nodes}
        success, response = self.make_request('POST', 'manual/ping-test-batch-progress', test_data)
        batch_response_time = time.time() - start_time
        
        # API should respond quickly (under 1 second) with session_id
        batch_ok = batch_response_time < 1.0 and success and 'session_id' in response
        self.log_test("Performance - Batch Response", batch_ok, 
                     f"Batch API response: {batch_response_time:.2f}s ({'✅ < 1s' if batch_ok else '❌ > 1s'})")
        
        return single_ok and batch_ok

    def run_tests(self):
        """Run the improved ping workflow tests"""
        print(f"\n🚀 Starting Improved Ping Workflow Testing")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 80)
        
        # Authentication tests
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Run improved ping workflow tests
        self.test_improved_ping_workflow()
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"🏁 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📊 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return False

if __name__ == "__main__":
    tester = PingWorkflowTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)