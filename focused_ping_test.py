#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class FocusedPingTester:
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
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
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

    def test_database_ping_functionality_review_request(self):
        """CRITICAL TEST: Database State and Ping Testing Functionality (Russian User Review Request)"""
        print("\n🔥 CRITICAL DATABASE PING FUNCTIONALITY TEST (Review Request)")
        print("=" * 80)
        
        # Step 1: Check current database status distribution
        print("\n📊 STEP 1: Database Status Check")
        stats_success, stats_response = self.make_request('GET', 'stats')
        
        if not stats_success or 'total' not in stats_response:
            self.log_test("Database Status Check", False, f"Failed to get stats: {stats_response}")
            return False
        
        total_nodes = stats_response['total']
        not_tested = stats_response.get('not_tested', 0)
        ping_ok = stats_response.get('ping_ok', 0)
        ping_failed = stats_response.get('ping_failed', 0)
        speed_ok = stats_response.get('speed_ok', 0)
        offline = stats_response.get('offline', 0)
        online = stats_response.get('online', 0)
        
        print(f"   📈 Current Database State:")
        print(f"      Total Nodes: {total_nodes}")
        print(f"      Not Tested: {not_tested}")
        print(f"      Ping OK: {ping_ok}")
        print(f"      Ping Failed: {ping_failed}")
        print(f"      Speed OK: {speed_ok}")
        print(f"      Offline: {offline}")
        print(f"      Online: {online}")
        
        if total_nodes == 0:
            self.log_test("Database Status Check", False, "No nodes in database - cannot test ping functionality")
            return False
        
        # Step 2: Get 3-5 random not_tested nodes for testing
        print(f"\n🎯 STEP 2: Select Random not_tested Nodes")
        nodes_success, nodes_response = self.make_request('GET', 'nodes?status=not_tested&limit=5')
        
        if not nodes_success or 'nodes' not in nodes_response:
            self.log_test("Get not_tested Nodes", False, f"Failed to get not_tested nodes: {nodes_response}")
            return False
        
        test_nodes = nodes_response['nodes']
        if not test_nodes:
            # If no not_tested nodes, get any nodes and test them
            print("   ⚠️  No not_tested nodes found, getting any available nodes...")
            nodes_success, nodes_response = self.make_request('GET', 'nodes?limit=5')
            if nodes_success and 'nodes' in nodes_response:
                test_nodes = nodes_response['nodes']
        
        if not test_nodes:
            self.log_test("Select Test Nodes", False, "No nodes available for testing")
            return False
        
        selected_nodes = test_nodes[:3]  # Use up to 3 nodes for focused testing
        node_ids = [node['id'] for node in selected_nodes]
        
        print(f"   📋 Selected {len(selected_nodes)} nodes for testing:")
        for i, node in enumerate(selected_nodes, 1):
            print(f"      {i}. Node {node['id']}: {node['ip']} (current status: {node['status']})")
        
        # Step 3: Test individual ping-test API
        print(f"\n🏓 STEP 3: Individual Ping Test API Verification")
        individual_results = []
        
        for node in selected_nodes[:2]:  # Test first 2 nodes individually
            node_id = node['id']
            original_status = node['status']
            
            print(f"   Testing Node {node_id} ({node['ip']})...")
            
            # Record timestamp before test
            before_test_time = time.time()
            
            ping_data = {"node_ids": [node_id]}
            ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
            
            # Record timestamp after test
            after_test_time = time.time()
            test_duration = after_test_time - before_test_time
            
            if ping_success and 'results' in ping_response and ping_response['results']:
                result = ping_response['results'][0]
                new_status = result.get('status')
                success = result.get('success', False)
                message = result.get('message', 'No message')
                ping_result = result.get('ping_result', {})
                
                print(f"      ✅ API Response: success={success}, status={original_status}→{new_status}")
                print(f"      📊 Ping Result: {ping_result}")
                print(f"      ⏱️  Test Duration: {test_duration:.2f}s")
                
                individual_results.append({
                    'node_id': node_id,
                    'ip': node['ip'],
                    'original_status': original_status,
                    'new_status': new_status,
                    'success': success,
                    'test_duration': test_duration,
                    'api_success': True
                })
            else:
                print(f"      ❌ API Failed: {ping_response}")
                individual_results.append({
                    'node_id': node_id,
                    'ip': node['ip'],
                    'original_status': original_status,
                    'new_status': None,
                    'success': False,
                    'test_duration': test_duration,
                    'api_success': False
                })
        
        # Step 4: Test batch ping-test API
        print(f"\n🚀 STEP 4: Batch Ping Test API Verification")
        
        batch_node_ids = node_ids[2:] if len(node_ids) > 2 else node_ids[:1]  # Use remaining nodes or just 1
        
        print(f"   Testing {len(batch_node_ids)} nodes in batch...")
        
        # Record timestamp before batch test
        before_batch_time = time.time()
        
        batch_data = {"node_ids": batch_node_ids}
        batch_success, batch_response = self.make_request('POST', 'manual/ping-test-batch', batch_data)
        
        # Record timestamp after batch test
        after_batch_time = time.time()
        batch_duration = after_batch_time - before_batch_time
        
        print(f"   ⏱️  Batch Test Duration: {batch_duration:.2f}s")
        
        batch_results = []
        if batch_success and 'results' in batch_response:
            print(f"   📊 Batch Results:")
            for result in batch_response['results']:
                node_id = result.get('node_id')
                success = result.get('success', False)
                status = result.get('status')
                message = result.get('message', 'No message')
                
                print(f"      Node {node_id}: success={success}, status={status}")
                batch_results.append({
                    'node_id': node_id,
                    'success': success,
                    'status': status,
                    'message': message
                })
        else:
            print(f"   ❌ Batch API Failed: {batch_response}")
        
        # Step 5: Verify database updates
        print(f"\n🗄️  STEP 5: Database Update Verification")
        
        # Wait a moment for database updates to complete
        time.sleep(2)
        
        # Check if node statuses were actually updated in database
        database_verification_success = True
        
        for result in individual_results + batch_results:
            if not result.get('node_id'):
                continue
                
            node_id = result['node_id']
            expected_status = result.get('new_status') or result.get('status')
            
            # Get current node status from database
            node_success, node_response = self.make_request('GET', f'nodes?limit=200')
            
            if node_success and 'nodes' in node_response:
                # Find our specific node
                current_node = None
                for node in node_response['nodes']:
                    if node['id'] == node_id:
                        current_node = node
                        break
                
                if current_node:
                    actual_status = current_node['status']
                    last_update = current_node.get('last_update', 'No timestamp')
                    
                    if expected_status and actual_status == expected_status:
                        print(f"      ✅ Node {node_id}: Status correctly updated to '{actual_status}' (last_update: {last_update})")
                    else:
                        print(f"      ❌ Node {node_id}: Status mismatch - Expected '{expected_status}', Got '{actual_status}'")
                        database_verification_success = False
                else:
                    print(f"      ❌ Node {node_id}: Not found in database")
                    database_verification_success = False
            else:
                print(f"      ❌ Failed to retrieve nodes from database")
                database_verification_success = False
        
        # Step 6: Check final database state
        print(f"\n📊 STEP 6: Final Database State Check")
        final_stats_success, final_stats_response = self.make_request('GET', 'stats')
        
        status_changes_detected = False
        if final_stats_success and 'total' in final_stats_response:
            final_not_tested = final_stats_response.get('not_tested', 0)
            final_ping_ok = final_stats_response.get('ping_ok', 0)
            final_ping_failed = final_stats_response.get('ping_failed', 0)
            
            print(f"   📈 Final Database State:")
            print(f"      Not Tested: {not_tested} → {final_not_tested} (Change: {final_not_tested - not_tested})")
            print(f"      Ping OK: {ping_ok} → {final_ping_ok} (Change: {final_ping_ok - ping_ok})")
            print(f"      Ping Failed: {ping_failed} → {final_ping_failed} (Change: {final_ping_failed - ping_failed})")
            
            # Verify that changes occurred
            status_changes_detected = (final_not_tested != not_tested or 
                                     final_ping_ok != ping_ok or 
                                     final_ping_failed != ping_failed)
            
            if status_changes_detected:
                print(f"      ✅ Status changes detected in database")
            else:
                print(f"      ⚠️  No status changes detected - this could indicate an issue")
        
        # Step 7: Performance and timeout analysis
        print(f"\n⚡ STEP 7: Performance Analysis")
        
        individual_avg_time = sum(r.get('test_duration', 0) for r in individual_results) / max(len(individual_results), 1)
        batch_per_node_time = batch_duration / max(len(batch_node_ids), 1)
        
        print(f"   📊 Performance Metrics:")
        print(f"      Individual Test Average: {individual_avg_time:.2f}s per node")
        print(f"      Batch Test Average: {batch_per_node_time:.2f}s per node")
        print(f"      Batch Total Duration: {batch_duration:.2f}s for {len(batch_node_ids)} nodes")
        
        # Check for potential timeout issues (>30s per node could cause 90% freeze)
        timeout_risk = individual_avg_time > 30 or batch_per_node_time > 30
        
        if timeout_risk:
            print(f"      ⚠️  TIMEOUT RISK DETECTED: Average test time >30s could cause modal freezing")
        else:
            print(f"      ✅ Performance acceptable: No timeout risk detected")
        
        # Final assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        
        issues_found = []
        
        # Check API functionality
        individual_api_success = all(r.get('api_success', False) for r in individual_results)
        batch_api_success = batch_success and 'results' in batch_response
        
        if not individual_api_success:
            issues_found.append("Individual ping-test API failures")
        
        if not batch_api_success:
            issues_found.append("Batch ping-test API failures")
        
        if not database_verification_success:
            issues_found.append("Database status updates not working correctly")
        
        if timeout_risk:
            issues_found.append("Performance issues that could cause 90% modal freezing")
        
        if not status_changes_detected:
            issues_found.append("No status changes detected in database after tests")
        
        if issues_found:
            self.log_test("Database Ping Functionality Review Request", False, 
                         f"CRITICAL ISSUES FOUND: {', '.join(issues_found)}")
            return False
        else:
            self.log_test("Database Ping Functionality Review Request", True, 
                         f"✅ ALL SYSTEMS WORKING: APIs functional, database updates working, performance acceptable, no 90% freeze risk detected")
            return True

    def run_focused_test(self):
        """Run focused ping functionality test"""
        print("🔥 STARTING FOCUSED PING FUNCTIONALITY TEST")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 80)
        
        # Test authentication
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Run the critical test
        success = self.test_database_ping_functionality_review_request()
        
        # Print summary
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return success

if __name__ == "__main__":
    tester = FocusedPingTester()
    success = tester.run_focused_test()
    sys.exit(0 if success else 1)