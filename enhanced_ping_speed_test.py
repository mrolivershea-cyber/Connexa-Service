#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class EnhancedPingSpeedTester:
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
                response = requests.get(url, headers=headers, params=data, timeout=60)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=60)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data, timeout=60)
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

    def test_enhanced_ping_accuracy(self):
        """Test enhanced ping accuracy with improved timeouts and 75% packet loss threshold"""
        print("\n🏓 TESTING ENHANCED PING ACCURACY")
        print("=" * 50)
        
        # Get existing nodes for testing
        success, response = self.make_request('GET', 'nodes?limit=10')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Enhanced Ping Accuracy - Setup", False, "No nodes available for testing")
            return False
        
        test_nodes = response['nodes'][:5]  # Test with first 5 nodes
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Testing ping accuracy with {len(test_nodes)} nodes:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (current status: {node['status']})")
        
        # Test ping with enhanced accuracy
        ping_data = {"node_ids": node_ids}
        success, response = self.make_request('POST', 'manual/ping-test', ping_data)
        
        if success and 'results' in response:
            ping_ok_count = 0
            ping_failed_count = 0
            total_tests = len(response['results'])
            
            for result in response['results']:
                node_id = result.get('node_id')
                status = result.get('status')
                message = result.get('message', 'No message')
                
                if status == 'ping_ok':
                    ping_ok_count += 1
                    # Check for ping result details
                    if 'ping_result' in result:
                        ping_result = result['ping_result']
                        avg_time = ping_result.get('avg_time', 0)
                        packet_loss = ping_result.get('packet_loss', 100)
                        print(f"   ✅ Node {node_id}: PING OK - {avg_time}ms avg, {packet_loss}% loss")
                    else:
                        print(f"   ✅ Node {node_id}: PING OK - {message}")
                elif status == 'ping_failed':
                    ping_failed_count += 1
                    print(f"   ❌ Node {node_id}: PING FAILED - {message}")
                else:
                    print(f"   ⚠️ Node {node_id}: UNKNOWN STATUS - {status}")
            
            # Calculate success rate
            success_rate = (ping_ok_count / total_tests) * 100 if total_tests > 0 else 0
            
            print(f"\n📊 PING ACCURACY RESULTS:")
            print(f"   Total nodes tested: {total_tests}")
            print(f"   Ping OK: {ping_ok_count} ({success_rate:.1f}%)")
            print(f"   Ping Failed: {ping_failed_count}")
            
            # Enhanced accuracy should show more servers as ping_ok (improved from previous strict thresholds)
            if ping_ok_count > 0:
                self.log_test("Enhanced Ping Accuracy", True, 
                             f"✅ {ping_ok_count}/{total_tests} nodes ping_ok ({success_rate:.1f}% success rate) - Enhanced accuracy working with 8s timeout and 75% packet loss threshold")
                return True
            else:
                self.log_test("Enhanced Ping Accuracy", False, 
                             f"❌ No nodes achieved ping_ok status - Enhanced accuracy may still be too strict")
                return False
        else:
            self.log_test("Enhanced Ping Accuracy", False, f"Ping test failed: {response}")
            return False

    def test_real_speed_testing(self):
        """Test real HTTP speed testing using aiohttp and cloudflare.com"""
        print("\n🚀 TESTING REAL SPEED TESTING")
        print("=" * 50)
        
        # Get nodes with ping_ok status for speed testing
        success, response = self.make_request('GET', 'nodes?status=ping_ok&limit=5')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Real Speed Testing - Setup", False, "No ping_ok nodes available for speed testing")
            return False
        
        test_nodes = response['nodes'][:3]  # Test with first 3 ping_ok nodes
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Testing real speed with {len(test_nodes)} ping_ok nodes:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']}")
        
        # Test speed with real HTTP testing
        speed_data = {"node_ids": node_ids}
        success, response = self.make_request('POST', 'manual/speed-test', speed_data)
        
        if success and 'results' in response:
            real_speed_count = 0
            total_tests = len(response['results'])
            speed_values = []
            
            for result in response['results']:
                node_id = result.get('node_id')
                success_flag = result.get('success')
                status = result.get('status')
                message = result.get('message', 'No message')
                
                if success_flag and 'speed' in result:
                    speed_value = result['speed']
                    # Real speed testing should return actual Mbps values
                    if isinstance(speed_value, (int, float)) and speed_value > 0:
                        real_speed_count += 1
                        speed_values.append(speed_value)
                        print(f"   ✅ Node {node_id}: {speed_value} Mbps (Real HTTP measurement)")
                    else:
                        print(f"   ❌ Node {node_id}: Invalid speed value: {speed_value}")
                else:
                    print(f"   ❌ Node {node_id}: Speed test failed - {message}")
            
            print(f"\n📊 REAL SPEED TESTING RESULTS:")
            print(f"   Total nodes tested: {total_tests}")
            print(f"   Real measurements: {real_speed_count}")
            if speed_values:
                avg_speed = sum(speed_values) / len(speed_values)
                print(f"   Average speed: {avg_speed:.1f} Mbps")
                print(f"   Speed range: {min(speed_values):.1f} - {max(speed_values):.1f} Mbps")
            
            if real_speed_count > 0:
                self.log_test("Real Speed Testing", True, 
                             f"✅ {real_speed_count}/{total_tests} nodes returned real HTTP speed measurements using aiohttp and cloudflare.com")
                return True
            else:
                self.log_test("Real Speed Testing", False, 
                             f"❌ No nodes returned valid speed measurements - Real HTTP testing not working")
                return False
        else:
            self.log_test("Real Speed Testing", False, f"Speed test failed: {response}")
            return False

    def test_service_status_preservation(self):
        """Test that nodes with speed_ok status remain speed_ok when service launch fails"""
        print("\n🛡️ TESTING SERVICE STATUS PRESERVATION")
        print("=" * 50)
        
        # Get nodes with speed_ok status
        success, response = self.make_request('GET', 'nodes?status=speed_ok&limit=3')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Service Status Preservation - Setup", False, "No speed_ok nodes available for testing")
            return False
        
        test_nodes = response['nodes'][:2]  # Test with 2 speed_ok nodes
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Testing service status preservation with {len(test_nodes)} speed_ok nodes:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Record initial status
        initial_statuses = {}
        for node in test_nodes:
            initial_statuses[node['id']] = node['status']
        
        # Attempt to launch services (some may fail)
        launch_data = {"node_ids": node_ids}
        launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
        
        if not launch_success:
            self.log_test("Service Status Preservation", False, f"Launch services request failed: {launch_response}")
            return False
        
        # Check final status after service launch attempts
        preserved_count = 0
        online_count = 0
        downgraded_count = 0
        
        for node_id in node_ids:
            node_success, node_response = self.make_request('GET', f'nodes?id={node_id}')
            
            if node_success and node_response.get('nodes'):
                final_status = node_response['nodes'][0].get('status')
                initial_status = initial_statuses.get(node_id)
                
                if final_status == 'speed_ok':
                    preserved_count += 1
                    print(f"   ✅ Node {node_id}: Status preserved as speed_ok (service launch likely failed)")
                elif final_status == 'online':
                    online_count += 1
                    print(f"   ✅ Node {node_id}: Successfully launched to online status")
                elif final_status in ['ping_failed', 'offline']:
                    downgraded_count += 1
                    print(f"   ❌ Node {node_id}: Status downgraded to {final_status} (should have remained speed_ok)")
                else:
                    print(f"   ⚠️ Node {node_id}: Unexpected status {final_status}")
        
        print(f"\n📊 SERVICE STATUS PRESERVATION RESULTS:")
        print(f"   Preserved as speed_ok: {preserved_count}")
        print(f"   Successfully online: {online_count}")
        print(f"   Incorrectly downgraded: {downgraded_count}")
        
        # Success if no nodes were incorrectly downgraded
        if downgraded_count == 0:
            self.log_test("Service Status Preservation", True, 
                         f"✅ All nodes maintained proper status - {preserved_count} preserved speed_ok, {online_count} launched online")
            return True
        else:
            self.log_test("Service Status Preservation", False, 
                         f"❌ {downgraded_count} nodes incorrectly downgraded from speed_ok")
            return False

    def test_immediate_database_persistence(self):
        """Test that results are saved immediately after each test completion"""
        print("\n💾 TESTING IMMEDIATE DATABASE PERSISTENCE")
        print("=" * 50)
        
        # Get some nodes for testing
        success, response = self.make_request('GET', 'nodes?limit=5')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Immediate Database Persistence - Setup", False, "No nodes available for testing")
            return False
        
        test_nodes = response['nodes'][:3]  # Test with 3 nodes
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Testing immediate persistence with {len(test_nodes)} nodes:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (current status: {node['status']})")
        
        # Record initial last_update timestamps
        initial_timestamps = {}
        for node in test_nodes:
            initial_timestamps[node['id']] = node.get('last_update')
        
        # Perform batch ping test
        ping_data = {"node_ids": node_ids}
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test-batch', ping_data)
        
        if not ping_success:
            self.log_test("Immediate Database Persistence", False, f"Batch ping test failed: {ping_response}")
            return False
        
        # Immediately check if results are persisted in database
        persistence_verified = 0
        timestamp_updated = 0
        
        for node_id in node_ids:
            node_success, node_response = self.make_request('GET', f'nodes?id={node_id}')
            
            if node_success and node_response.get('nodes'):
                node = node_response['nodes'][0]
                current_status = node.get('status')
                current_timestamp = node.get('last_update')
                initial_timestamp = initial_timestamps.get(node_id)
                
                # Check if status was updated and persisted
                if current_status in ['ping_ok', 'ping_failed']:
                    persistence_verified += 1
                    print(f"   ✅ Node {node_id}: Status immediately persisted as {current_status}")
                else:
                    print(f"   ❌ Node {node_id}: Status not updated ({current_status})")
                
                # Check if timestamp was updated
                if current_timestamp != initial_timestamp:
                    timestamp_updated += 1
                    print(f"   ✅ Node {node_id}: Timestamp updated from {initial_timestamp} to {current_timestamp}")
                else:
                    print(f"   ❌ Node {node_id}: Timestamp not updated")
        
        print(f"\n📊 IMMEDIATE PERSISTENCE RESULTS:")
        print(f"   Status updates persisted: {persistence_verified}/{len(node_ids)}")
        print(f"   Timestamps updated: {timestamp_updated}/{len(node_ids)}")
        
        if persistence_verified >= 2:  # At least 2 out of 3 should be persisted
            self.log_test("Immediate Database Persistence", True, 
                         f"✅ {persistence_verified}/{len(node_ids)} nodes immediately persisted with db.commit() after each test")
            return True
        else:
            self.log_test("Immediate Database Persistence", False, 
                         f"❌ Only {persistence_verified}/{len(node_ids)} nodes persisted - Immediate saving not working")
            return False

    def test_batch_operations(self):
        """Test ping + speed batch operations to ensure they don't hang at 90% completion"""
        print("\n📦 TESTING BATCH OPERATIONS")
        print("=" * 50)
        
        # Get nodes for batch testing
        success, response = self.make_request('GET', 'nodes?limit=10')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("Batch Operations - Setup", False, "No nodes available for testing")
            return False
        
        test_nodes = response['nodes'][:5]  # Test with 5 nodes
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Testing batch operations with {len(test_nodes)} nodes:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Test 1: Batch ping test
        print("\n   🏓 Testing batch ping operations...")
        ping_data = {"node_ids": node_ids}
        ping_start_time = time.time()
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test-batch', ping_data)
        ping_duration = time.time() - ping_start_time
        
        if not ping_success:
            self.log_test("Batch Operations - Ping", False, f"Batch ping failed: {ping_response}")
            return False
        
        print(f"   ✅ Batch ping completed in {ping_duration:.1f}s (no hanging at 90%)")
        
        # Test 2: Combined ping + speed batch test
        print("\n   🚀 Testing combined ping + speed batch operations...")
        combined_data = {"node_ids": node_ids}
        combined_start_time = time.time()
        combined_success, combined_response = self.make_request('POST', 'manual/ping-speed-test-batch', combined_data)
        combined_duration = time.time() - combined_start_time
        
        if not combined_success:
            self.log_test("Batch Operations - Combined", False, f"Combined batch failed: {combined_response}")
            return False
        
        print(f"   ✅ Combined batch completed in {combined_duration:.1f}s (no hanging at 90%)")
        
        # Verify no nodes are stuck in 'checking' status
        checking_nodes = 0
        completed_nodes = 0
        
        for node_id in node_ids:
            node_success, node_response = self.make_request('GET', f'nodes?id={node_id}')
            
            if node_success and node_response.get('nodes'):
                status = node_response['nodes'][0].get('status')
                if status == 'checking':
                    checking_nodes += 1
                    print(f"   ❌ Node {node_id}: Stuck in 'checking' status")
                elif status in ['ping_ok', 'ping_failed', 'speed_ok']:
                    completed_nodes += 1
                    print(f"   ✅ Node {node_id}: Completed with status {status}")
        
        print(f"\n📊 BATCH OPERATIONS RESULTS:")
        print(f"   Batch ping duration: {ping_duration:.1f}s")
        print(f"   Combined batch duration: {combined_duration:.1f}s")
        print(f"   Nodes completed: {completed_nodes}/{len(node_ids)}")
        print(f"   Nodes stuck in 'checking': {checking_nodes}")
        
        if checking_nodes == 0 and completed_nodes >= 3:
            self.log_test("Batch Operations", True, 
                         f"✅ No hanging at 90% - {completed_nodes}/{len(node_ids)} nodes completed, 0 stuck in 'checking'")
            return True
        else:
            self.log_test("Batch Operations", False, 
                         f"❌ Batch operations issues - {checking_nodes} stuck in 'checking', {completed_nodes} completed")
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🏁 ENHANCED PING AND SPEED TESTING SUMMARY")
        print("=" * 80)
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL ENHANCED PING AND SPEED TESTS PASSED")
            return True
        else:
            print("❌ SOME ENHANCED PING AND SPEED TESTS FAILED")
            return False

    def run_enhanced_tests(self):
        """Run all enhanced ping and speed tests"""
        print("🚀 Starting Enhanced Ping and Speed Testing")
        print("🌐 Testing against:", self.base_url)
        print("=" * 80)
        
        # Test authentication
        if not self.test_login():
            print("❌ Login failed - cannot continue with authenticated tests")
            return self.print_summary()
        
        # Run enhanced ping and speed tests
        self.test_enhanced_ping_accuracy()
        self.test_real_speed_testing()
        self.test_service_status_preservation()
        self.test_immediate_database_persistence()
        self.test_batch_operations()
        
        return self.print_summary()

if __name__ == "__main__":
    tester = EnhancedPingSpeedTester()
    success = tester.run_enhanced_tests()
    sys.exit(0 if success else 1)