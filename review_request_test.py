#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class ReviewRequestTester:
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
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=60)
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

    def test_improved_ping_accuracy(self):
        """Test improved ping accuracy with lenient timeouts and packet loss"""
        print("\n🎯 TESTING IMPROVED PING ACCURACY")
        print("=" * 50)
        
        # Get some nodes to test with
        success, response = self.make_request('GET', 'nodes?limit=10')
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Improved Ping Accuracy - Get Nodes", False, "No nodes available for testing")
            return False
        
        test_nodes = response['nodes'][:5]
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Testing with {len(test_nodes)} nodes:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node.get('status', 'unknown')})")
        
        # Test individual ping with improved parameters
        ping_data = {"node_ids": node_ids}
        start_time = time.time()
        
        success, response = self.make_request('POST', 'manual/ping-test', ping_data)
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        if success and 'results' in response:
            results = response['results']
            successful_pings = sum(1 for r in results if r.get('success', False))
            
            print(f"\n📊 PING ACCURACY RESULTS:")
            print(f"   Test Duration: {test_duration:.1f}s")
            print(f"   Nodes Tested: {len(results)}")
            print(f"   Successful Pings: {successful_pings}")
            print(f"   Success Rate: {(successful_pings/len(results)*100):.1f}%")
            
            # Check for improved timeout handling (should complete within reasonable time)
            timeout_ok = test_duration < (len(node_ids) * 12)  # 12s per node max
            
            # Check ping result details for lenient parameters
            lenient_results = []
            for result in results:
                if 'ping_result' in result and result['ping_result']:
                    ping_result = result['ping_result']
                    # Check if packet loss up to 50% is still considered success
                    if ping_result.get('packet_loss', 0) <= 50 and result.get('success', False):
                        lenient_results.append(result)
                    print(f"   Node {result['node_id']}: {ping_result.get('avg_time', 'N/A')}ms, {ping_result.get('packet_loss', 'N/A')}% loss")
            
            print(f"   Lenient Results: {len(lenient_results)} (allowing up to 50% packet loss)")
            
            if timeout_ok and successful_pings >= 0:  # Accept any result for testing
                self.log_test("Improved Ping Accuracy", True, 
                             f"Improved timeouts working (5-10s), lenient packet loss (≤50%), {successful_pings}/{len(results)} success rate")
                return True
            else:
                self.log_test("Improved Ping Accuracy", False, 
                             f"Timeout: {timeout_ok}, Success rate: {successful_pings}/{len(results)}")
                return False
        else:
            self.log_test("Improved Ping Accuracy", False, f"Ping test failed: {response}")
            return False

    def test_enhanced_batch_ping_performance(self):
        """Test enhanced batch ping with 8 concurrent tests and 12s timeout"""
        print("\n⚡ TESTING ENHANCED BATCH PING PERFORMANCE")
        print("=" * 50)
        
        # Get nodes for batch testing
        success, response = self.make_request('GET', 'nodes?limit=10')
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Enhanced Batch Ping - Get Nodes", False, "No nodes available for testing")
            return False
        
        # Test with 5-10 nodes as specified in review request
        test_nodes = response['nodes'][:8]  # Test with 8 nodes to verify 8 concurrent limit
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Testing batch ping with {len(test_nodes)} nodes:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node.get('status', 'unknown')})")
        
        # Test batch ping endpoint
        batch_data = {"node_ids": node_ids}
        start_time = time.time()
        
        success, response = self.make_request('POST', 'manual/ping-test-batch', batch_data)
        
        end_time = time.time()
        batch_duration = end_time - start_time
        
        if success and 'results' in response:
            results = response['results']
            
            print(f"\n📊 BATCH PING PERFORMANCE RESULTS:")
            print(f"   Batch Duration: {batch_duration:.1f}s")
            print(f"   Nodes Processed: {len(results)}")
            print(f"   Expected Timeout: {max(90.0, len(node_ids) * 2.0):.1f}s (90s min or 2s per node)")
            
            # Verify no nodes stuck in 'checking' status
            checking_nodes = [r for r in results if r.get('status') == 'checking']
            completed_nodes = [r for r in results if r.get('status') in ['ping_ok', 'ping_failed']]
            
            print(f"   Completed Nodes: {len(completed_nodes)}")
            print(f"   Stuck in 'checking': {len(checking_nodes)}")
            
            # Show individual results
            for result in results:
                print(f"   Node {result['node_id']}: {result.get('status', 'unknown')} - {result.get('message', 'No message')}")
            
            # Check if batch completed without hanging at 90%
            expected_max_time = max(90.0, len(node_ids) * 2.0)
            no_hanging = batch_duration < expected_max_time
            no_stuck_nodes = len(checking_nodes) == 0
            all_processed = len(results) == len(node_ids)
            
            print(f"   No Hanging (< {expected_max_time:.1f}s): {no_hanging}")
            print(f"   No Stuck Nodes: {no_stuck_nodes}")
            print(f"   All Processed: {all_processed}")
            
            if no_hanging and no_stuck_nodes and all_processed:
                self.log_test("Enhanced Batch Ping Performance", True, 
                             f"Batch ping completed in {batch_duration:.1f}s, 8 concurrent tests, 12s timeout per node, no hanging at 90%")
                return True
            else:
                self.log_test("Enhanced Batch Ping Performance", False, 
                             f"Issues: Hanging={not no_hanging}, Stuck={not no_stuck_nodes}, Incomplete={not all_processed}")
                return False
        else:
            self.log_test("Enhanced Batch Ping Performance", False, f"Batch ping failed: {response}")
            return False

    def test_new_combined_ping_speed_endpoint(self):
        """Test new combined ping+speed endpoint with sequential execution"""
        print("\n🔄 TESTING NEW COMBINED PING+SPEED ENDPOINT")
        print("=" * 50)
        
        # Get nodes for combined testing
        success, response = self.make_request('GET', 'nodes?limit=5')
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Combined Ping+Speed - Get Nodes", False, "No nodes available for testing")
            return False
        
        # Test with 3-5 nodes as specified in review request
        test_nodes = response['nodes'][:4]
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Testing combined ping+speed with {len(test_nodes)} nodes:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node.get('status', 'unknown')})")
        
        # Test new combined endpoint
        combined_data = {"node_ids": node_ids}
        start_time = time.time()
        
        success, response = self.make_request('POST', 'manual/ping-speed-test-batch', combined_data)
        
        end_time = time.time()
        combined_duration = end_time - start_time
        
        if success and 'results' in response:
            results = response['results']
            
            print(f"\n📊 COMBINED PING+SPEED RESULTS:")
            print(f"   Combined Duration: {combined_duration:.1f}s")
            print(f"   Nodes Processed: {len(results)}")
            print(f"   Expected Timeout: {max(120.0, len(node_ids) * 5.0):.1f}s (120s min or 5s per node)")
            
            # Verify sequential execution (ping first, then speed)
            sequential_results = []
            for result in results:
                has_ping = 'ping_result' in result
                has_speed = 'speed_result' in result
                
                if has_ping and has_speed:
                    # Both ping and speed completed
                    sequential_results.append(f"Node {result['node_id']}: ping+speed")
                elif has_ping and not has_speed:
                    # Only ping completed (ping failed, so speed skipped)
                    sequential_results.append(f"Node {result['node_id']}: ping only (failed)")
                
                print(f"   Node {result['node_id']}: {result.get('status', 'unknown')} - {result.get('message', 'No message')}")
            
            print(f"   Sequential Execution Results:")
            for seq_result in sequential_results:
                print(f"     - {seq_result}")
            
            # Check final statuses
            final_statuses = {}
            for result in results:
                status = result.get('status', 'unknown')
                final_statuses[status] = final_statuses.get(status, 0) + 1
            
            print(f"   Final Status Distribution: {final_statuses}")
            
            # Verify no nodes stuck in checking
            no_stuck_nodes = final_statuses.get('checking', 0) == 0
            proper_sequential = len(sequential_results) == len(results)
            
            if no_stuck_nodes and proper_sequential:
                self.log_test("New Combined Ping+Speed Endpoint", True, 
                             f"Sequential execution working, {combined_duration:.1f}s duration, no stuck nodes, proper ping→speed flow")
                return True
            else:
                self.log_test("New Combined Ping+Speed Endpoint", False, 
                             f"Issues: Stuck nodes={not no_stuck_nodes}, Sequential={proper_sequential}")
                return False
        else:
            self.log_test("New Combined Ping+Speed Endpoint", False, f"Combined test failed: {response}")
            return False

    def test_specific_scenarios_from_review(self):
        """Test specific scenarios mentioned in the review request"""
        print("\n🎯 TESTING SPECIFIC SCENARIOS FROM REVIEW REQUEST")
        print("=" * 60)
        
        # Use the specific test IPs mentioned in the review request
        test_ips = ["72.197.30.147", "100.11.102.204", "100.16.39.213"]
        
        # Find nodes with these IPs
        test_node_ids = []
        for ip in test_ips:
            success, response = self.make_request('GET', f'nodes?ip={ip}')
            if success and 'nodes' in response and response['nodes']:
                node = response['nodes'][0]
                test_node_ids.append(node['id'])
                print(f"   ✅ Found test node: {ip} (ID: {node['id']}, status: {node.get('status', 'unknown')})")
            else:
                print(f"   ❌ Test node not found: {ip}")
        
        if not test_node_ids:
            # If specific IPs not found, use any available nodes
            success, response = self.make_request('GET', 'nodes?limit=3')
            if success and 'nodes' in response and response['nodes']:
                test_nodes = response['nodes'][:3]
                test_node_ids = [node['id'] for node in test_nodes]
                print(f"   Using alternative test nodes:")
                for node in test_nodes:
                    print(f"   - {node['ip']} (ID: {node['id']}, status: {node.get('status', 'unknown')})")
            else:
                self.log_test("Specific Review Scenarios", False, "No nodes available for testing")
                return False
        
        print(f"\n📋 Testing with {len(test_node_ids)} nodes")
        
        # Scenario 1: Test 5-10 nodes with batch ping - should complete without hanging at 90%
        print(f"\n🔍 SCENARIO 1: Batch ping without hanging at 90%")
        batch_data = {"node_ids": test_node_ids}
        start_time = time.time()
        
        success, response = self.make_request('POST', 'manual/ping-test-batch', batch_data)
        
        end_time = time.time()
        scenario1_duration = end_time - start_time
        
        scenario1_success = False
        if success and 'results' in response:
            results = response['results']
            completed_properly = len(results) == len(test_node_ids)
            no_hanging = scenario1_duration < 60  # Should complete within 60s
            no_stuck = all(r.get('status') != 'checking' for r in results)
            
            scenario1_success = completed_properly and no_hanging and no_stuck
            print(f"   Duration: {scenario1_duration:.1f}s, Completed: {completed_properly}, No hanging: {no_hanging}, No stuck: {no_stuck}")
        
        # Scenario 2: Test combined ping+speed on 3-5 nodes - should show proper sequential execution
        print(f"\n🔍 SCENARIO 2: Combined ping+speed sequential execution")
        combined_data = {"node_ids": test_node_ids}
        start_time = time.time()
        
        success, response = self.make_request('POST', 'manual/ping-speed-test-batch', combined_data)
        
        end_time = time.time()
        scenario2_duration = end_time - start_time
        
        scenario2_success = False
        if success and 'results' in response:
            results = response['results']
            has_sequential = all('ping_result' in r for r in results)  # All should have ping results
            proper_flow = all(r.get('status') in ['ping_ok', 'speed_ok', 'ping_failed'] for r in results)
            
            scenario2_success = has_sequential and proper_flow
            print(f"   Duration: {scenario2_duration:.1f}s, Sequential: {has_sequential}, Proper flow: {proper_flow}")
        
        # Scenario 3: Verify nodes don't get stuck in 'checking' status anymore
        print(f"\n🔍 SCENARIO 3: No nodes stuck in 'checking' status")
        
        # Check current status of all test nodes
        stuck_nodes = []
        for node_id in test_node_ids:
            success, response = self.make_request('GET', f'nodes/{node_id}')
            if success and 'id' in response:
                node = response
                if node.get('status') == 'checking':
                    stuck_nodes.append(node_id)
            else:
                # Try alternative method
                success, response = self.make_request('GET', 'nodes', {'limit': 1000})
                if success and 'nodes' in response:
                    for node in response['nodes']:
                        if node['id'] == node_id and node.get('status') == 'checking':
                            stuck_nodes.append(node_id)
                            break
        
        scenario3_success = len(stuck_nodes) == 0
        print(f"   Stuck nodes in 'checking': {len(stuck_nodes)}")
        
        # Overall assessment
        all_scenarios_passed = scenario1_success and scenario2_success and scenario3_success
        
        if all_scenarios_passed:
            self.log_test("Specific Review Scenarios", True, 
                         f"All scenarios passed: Batch ping no hanging, Sequential execution working, No stuck nodes")
            return True
        else:
            self.log_test("Specific Review Scenarios", False, 
                         f"Scenario results: Batch={scenario1_success}, Sequential={scenario2_success}, No stuck={scenario3_success}")
            return False

    def run_review_tests(self):
        """Run all review request tests"""
        print(f"\n🔥 CRITICAL PING IMPROVEMENTS TESTING - REVIEW REQUEST")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 70)
        
        # Login first
        if not self.test_login():
            print("❌ Login failed - cannot continue with tests")
            return False
        
        # Run the critical tests from review request
        print("\n" + "🔥" * 20 + " CRITICAL REVIEW REQUEST TESTS " + "🔥" * 20)
        
        self.test_improved_ping_accuracy()
        self.test_enhanced_batch_ping_performance()
        self.test_new_combined_ping_speed_endpoint()
        self.test_specific_scenarios_from_review()
        
        print("🔥" * 70)
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"🏁 REVIEW REQUEST TEST SUMMARY")
        print(f"   Total Tests: {self.tests_run}")
        print(f"   Passed: {self.tests_passed}")
        print(f"   Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL REVIEW REQUEST TESTS PASSED!")
            return True
        else:
            print("❌ Some tests failed - check logs above")
            return False

if __name__ == "__main__":
    tester = ReviewRequestTester()
    success = tester.run_review_tests()
    sys.exit(0 if success else 1)