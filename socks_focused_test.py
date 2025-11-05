#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class SOCKSFocusedTester:
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

    def test_socks_stats_detailed(self):
        """Test SOCKS stats endpoint with detailed analysis"""
        print("\n🔍 DETAILED SOCKS STATS ANALYSIS")
        print("=" * 50)
        
        success, response = self.make_request('GET', 'socks/stats')
        
        if success:
            print(f"📊 SOCKS Statistics:")
            print(f"   online_socks: {response.get('online_socks', 'N/A')}")
            print(f"   total_tunnels: {response.get('total_tunnels', 'N/A')}")
            print(f"   active_connections: {response.get('active_connections', 'N/A')}")
            print(f"   socks_enabled_nodes: {response.get('socks_enabled_nodes', 'N/A')}")
            
            self.log_test("SOCKS Stats Detailed", True, 
                         f"Stats retrieved successfully")
            return response
        else:
            self.log_test("SOCKS Stats Detailed", False, f"Failed to get SOCKS stats: {response}")
            return None

    def test_socks_start_with_real_nodes(self):
        """Test SOCKS start with real nodes that have ping_ok or speed_ok status"""
        print("\n🚀 SOCKS START WITH REAL NODES TEST")
        print("=" * 50)
        
        # Step 1: Find nodes with ping_ok or speed_ok status
        success, response = self.make_request('GET', 'nodes?status=ping_ok&limit=5')
        ping_ok_nodes = []
        if success and 'nodes' in response:
            ping_ok_nodes = response['nodes']
        
        success, response = self.make_request('GET', 'nodes?status=speed_ok&limit=5')
        speed_ok_nodes = []
        if success and 'nodes' in response:
            speed_ok_nodes = response['nodes']
        
        # Combine and prioritize speed_ok nodes
        suitable_nodes = speed_ok_nodes + ping_ok_nodes
        
        if not suitable_nodes:
            self.log_test("SOCKS Start - Find Suitable Nodes", False, 
                         "No nodes with ping_ok or speed_ok status found")
            return False
        
        # Take first 3 nodes for testing
        test_nodes = suitable_nodes[:3]
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📋 Testing SOCKS start with {len(test_nodes)} suitable nodes:")
        for i, node in enumerate(test_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Step 2: Test SOCKS start
        start_data = {
            "node_ids": node_ids,
            "masking_settings": {
                "obfuscation": True,
                "http_imitation": True,
                "timing_randomization": True,
                "tunnel_encryption": True
            },
            "performance_settings": {
                "tunnel_limit": 100,
                "auto_scaling": True,
                "cpu_threshold": 80,
                "ram_threshold": 90
            },
            "security_settings": {
                "whitelist_enabled": False,
                "allowed_ips": []
            }
        }
        
        success, response = self.make_request('POST', 'socks/start', start_data)
        
        if success and 'results' in response:
            successful_starts = 0
            failed_starts = 0
            
            print(f"\n📊 SOCKS Start Results:")
            for result in response['results']:
                node_id = result['node_id']
                success_flag = result.get('success', False)
                message = result.get('message', 'No message')
                status = result.get('status', 'Unknown')
                
                print(f"   Node {node_id}: {'✅' if success_flag else '❌'} {message} (status: {status})")
                
                if success_flag:
                    successful_starts += 1
                    # Check for SOCKS credentials
                    if 'socks_ip' in result and 'socks_port' in result:
                        print(f"      SOCKS: {result['socks_ip']}:{result['socks_port']} ({result.get('socks_login', 'N/A')}/***)")
                else:
                    failed_starts += 1
            
            print(f"\n📈 Summary: {successful_starts} successful, {failed_starts} failed")
            
            if successful_starts > 0:
                self.log_test("SOCKS Start - Real Nodes", True, 
                             f"Successfully started SOCKS on {successful_starts}/{len(test_nodes)} nodes")
                return True
            else:
                self.log_test("SOCKS Start - Real Nodes", False, 
                             f"Failed to start SOCKS on any nodes. All {failed_starts} attempts failed")
                return False
        else:
            self.log_test("SOCKS Start - Real Nodes", False, f"SOCKS start request failed: {response}")
            return False

    def test_socks_start_node_selection_logic(self):
        """Test the node selection logic for SOCKS start"""
        print("\n🎯 SOCKS NODE SELECTION LOGIC TEST")
        print("=" * 50)
        
        # Test 1: Try to start SOCKS with not_tested nodes (should fail)
        success, response = self.make_request('GET', 'nodes?status=not_tested&limit=2')
        if success and 'nodes' in response and response['nodes']:
            not_tested_nodes = response['nodes'][:2]
            node_ids = [node['id'] for node in not_tested_nodes]
            
            print(f"🔍 Test 1: Attempting SOCKS start with not_tested nodes: {node_ids}")
            
            start_data = {
                "node_ids": node_ids,
                "masking_settings": {"obfuscation": False},
                "performance_settings": {"tunnel_limit": 50},
                "security_settings": {"whitelist_enabled": False}
            }
            
            success, response = self.make_request('POST', 'socks/start', start_data)
            
            if success and 'results' in response:
                rejected_count = 0
                for result in response['results']:
                    if not result.get('success') and 'wrong status' in result.get('message', '').lower():
                        rejected_count += 1
                
                if rejected_count == len(node_ids):
                    self.log_test("SOCKS Start - Node Selection (not_tested rejection)", True, 
                                 f"Correctly rejected {rejected_count} not_tested nodes")
                else:
                    self.log_test("SOCKS Start - Node Selection (not_tested rejection)", False, 
                                 f"Should reject all not_tested nodes, but only rejected {rejected_count}/{len(node_ids)}")
            else:
                self.log_test("SOCKS Start - Node Selection (not_tested rejection)", False, 
                             f"Request failed: {response}")
        
        # Test 2: Try to start SOCKS with ping_failed nodes (should fail)
        success, response = self.make_request('GET', 'nodes?status=ping_failed&limit=2')
        if success and 'nodes' in response and response['nodes']:
            ping_failed_nodes = response['nodes'][:2]
            node_ids = [node['id'] for node in ping_failed_nodes]
            
            print(f"🔍 Test 2: Attempting SOCKS start with ping_failed nodes: {node_ids}")
            
            start_data = {
                "node_ids": node_ids,
                "masking_settings": {"obfuscation": False},
                "performance_settings": {"tunnel_limit": 50},
                "security_settings": {"whitelist_enabled": False}
            }
            
            success, response = self.make_request('POST', 'socks/start', start_data)
            
            if success and 'results' in response:
                rejected_count = 0
                for result in response['results']:
                    if not result.get('success') and 'wrong status' in result.get('message', '').lower():
                        rejected_count += 1
                
                if rejected_count == len(node_ids):
                    self.log_test("SOCKS Start - Node Selection (ping_failed rejection)", True, 
                                 f"Correctly rejected {rejected_count} ping_failed nodes")
                else:
                    self.log_test("SOCKS Start - Node Selection (ping_failed rejection)", False, 
                                 f"Should reject all ping_failed nodes, but only rejected {rejected_count}/{len(node_ids)}")
            else:
                self.log_test("SOCKS Start - Node Selection (ping_failed rejection)", False, 
                             f"Request failed: {response}")

    def test_socks_credentials_generation(self):
        """Test SOCKS credentials generation (ports, logins, passwords)"""
        print("\n🔐 SOCKS CREDENTIALS GENERATION TEST")
        print("=" * 50)
        
        # Get nodes that are currently online (should have SOCKS credentials)
        success, response = self.make_request('GET', 'nodes?status=online&limit=5')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("SOCKS Credentials - Get Online Nodes", False, 
                         "No online nodes found to check credentials")
            return False
        
        online_nodes = response['nodes']
        credentials_valid = 0
        credentials_invalid = 0
        
        print(f"🔍 Checking SOCKS credentials for {len(online_nodes)} online nodes:")
        
        for i, node in enumerate(online_nodes, 1):
            socks_ip = node.get('socks_ip')
            socks_port = node.get('socks_port')
            socks_login = node.get('socks_login')
            socks_password = node.get('socks_password')
            
            print(f"   {i}. Node {node['id']}: {node['ip']}")
            
            # Validate credentials
            has_ip = socks_ip is not None
            has_port = socks_port is not None and 1081 <= int(socks_port) <= 9999
            has_login = socks_login is not None and socks_login.startswith('socks_')
            has_password = socks_password is not None and len(socks_password) == 16
            
            if has_ip and has_port and has_login and has_password:
                credentials_valid += 1
                print(f"      ✅ SOCKS: {socks_ip}:{socks_port} ({socks_login}/***) - Valid")
            else:
                credentials_invalid += 1
                print(f"      ❌ SOCKS: IP={has_ip}, Port={has_port}, Login={has_login}, Password={has_password}")
        
        if credentials_valid > 0:
            self.log_test("SOCKS Credentials Generation", True, 
                         f"{credentials_valid}/{len(online_nodes)} nodes have valid SOCKS credentials")
            return True
        else:
            self.log_test("SOCKS Credentials Generation", False, 
                         f"No nodes have valid SOCKS credentials. {credentials_invalid} nodes have invalid credentials")
            return False

    def test_socks_proxy_file_generation(self):
        """Test SOCKS proxy file generation and format"""
        print("\n📄 SOCKS PROXY FILE GENERATION TEST")
        print("=" * 50)
        
        success, response = self.make_request('GET', 'socks/proxy-file')
        
        if success and 'content' in response:
            content = response['content']
            lines = content.split('\n')
            
            print(f"📄 Proxy file content ({len(lines)} lines):")
            
            # Check for header
            has_header = any('Активные SOCKS прокси' in line for line in lines)
            
            # Count valid proxy lines
            valid_proxy_lines = 0
            for line in lines:
                if line.strip() and line.startswith('socks5://'):
                    # Format should be: socks5://login:password@ip:port
                    if '@' in line and ':' in line:
                        valid_proxy_lines += 1
                        print(f"   ✅ {line}")
            
            print(f"\n📊 Analysis:")
            print(f"   Header present: {'✅' if has_header else '❌'}")
            print(f"   Valid proxy lines: {valid_proxy_lines}")
            
            if has_header and valid_proxy_lines > 0:
                self.log_test("SOCKS Proxy File Generation", True, 
                             f"Proxy file generated with header and {valid_proxy_lines} valid proxy lines")
                return True
            else:
                self.log_test("SOCKS Proxy File Generation", False, 
                             f"Proxy file issues: Header={has_header}, Valid lines={valid_proxy_lines}")
                return False
        else:
            self.log_test("SOCKS Proxy File Generation", False, f"Failed to get proxy file: {response}")
            return False

    def test_socks_stop_and_cleanup(self):
        """Test SOCKS stop functionality and cleanup"""
        print("\n🛑 SOCKS STOP AND CLEANUP TEST")
        print("=" * 50)
        
        # Get online nodes (nodes with active SOCKS)
        success, response = self.make_request('GET', 'nodes?status=online&limit=3')
        
        if not success or 'nodes' not in response or not response['nodes']:
            self.log_test("SOCKS Stop - Get Online Nodes", False, 
                         "No online nodes found to test SOCKS stop")
            return False
        
        online_nodes = response['nodes'][:3]
        node_ids = [node['id'] for node in online_nodes]
        
        print(f"📋 Testing SOCKS stop with {len(online_nodes)} online nodes:")
        for i, node in enumerate(online_nodes, 1):
            print(f"   {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        
        # Record initial SOCKS data
        initial_socks_data = {}
        for node in online_nodes:
            initial_socks_data[node['id']] = {
                'socks_ip': node.get('socks_ip'),
                'socks_port': node.get('socks_port'),
                'socks_login': node.get('socks_login'),
                'socks_password': node.get('socks_password')
            }
        
        # Test SOCKS stop
        stop_data = {"node_ids": node_ids}
        success, response = self.make_request('POST', 'socks/stop', stop_data)
        
        if success and 'results' in response:
            successful_stops = 0
            failed_stops = 0
            
            print(f"\n📊 SOCKS Stop Results:")
            for result in response['results']:
                node_id = result['node_id']
                success_flag = result.get('success', False)
                message = result.get('message', 'No message')
                status = result.get('status', 'Unknown')
                
                print(f"   Node {node_id}: {'✅' if success_flag else '❌'} {message} (status: {status})")
                
                if success_flag:
                    successful_stops += 1
                else:
                    failed_stops += 1
            
            # Verify cleanup by checking nodes again
            print(f"\n🔍 Verifying SOCKS data cleanup:")
            cleanup_verified = 0
            
            for node_id in node_ids:
                success, response = self.make_request('GET', f'nodes?id={node_id}')
                if success and 'nodes' in response and response['nodes']:
                    node = response['nodes'][0]
                    
                    # Check if SOCKS fields are cleared
                    socks_cleared = all(
                        node.get(field) is None 
                        for field in ['socks_ip', 'socks_port', 'socks_login', 'socks_password']
                    )
                    
                    if socks_cleared:
                        cleanup_verified += 1
                        print(f"   ✅ Node {node_id}: SOCKS data cleared")
                    else:
                        print(f"   ❌ Node {node_id}: SOCKS data not cleared")
            
            print(f"\n📈 Summary: {successful_stops} successful stops, {cleanup_verified} cleanups verified")
            
            if successful_stops > 0 and cleanup_verified > 0:
                self.log_test("SOCKS Stop and Cleanup", True, 
                             f"Successfully stopped SOCKS on {successful_stops} nodes and verified {cleanup_verified} cleanups")
                return True
            else:
                self.log_test("SOCKS Stop and Cleanup", False, 
                             f"Issues with SOCKS stop: {successful_stops} stops, {cleanup_verified} cleanups")
                return False
        else:
            self.log_test("SOCKS Stop and Cleanup", False, f"SOCKS stop request failed: {response}")
            return False

    def test_socks_integration_with_stats(self):
        """Test SOCKS integration with main stats API"""
        print("\n📊 SOCKS INTEGRATION WITH MAIN STATS TEST")
        print("=" * 50)
        
        success, response = self.make_request('GET', 'stats')
        
        if success and 'socks_online' in response:
            socks_online = response['socks_online']
            total = response.get('total', 0)
            online = response.get('online', 0)
            
            print(f"📊 Main Stats API:")
            print(f"   Total nodes: {total}")
            print(f"   Online nodes: {online}")
            print(f"   SOCKS online: {socks_online}")
            
            # Verify that socks_online <= online
            if socks_online <= online:
                self.log_test("SOCKS Integration with Main Stats", True, 
                             f"SOCKS online ({socks_online}) <= Online nodes ({online}) - Integration working")
                return True
            else:
                self.log_test("SOCKS Integration with Main Stats", False, 
                             f"SOCKS online ({socks_online}) > Online nodes ({online}) - Integration issue")
                return False
        else:
            self.log_test("SOCKS Integration with Main Stats", False, 
                         f"Main stats API missing socks_online field: {response}")
            return False

    def run_comprehensive_socks_focused_tests(self):
        """Run all SOCKS focused tests addressing Russian user's concern"""
        print("🇷🇺 RUSSIAN USER SOCKS ISSUE INVESTIGATION")
        print("=" * 80)
        print("Issue: 'Не запускается сокс' (SOCKS won't start)")
        print("Focus: Comprehensive testing of SOCKS start functionality")
        print("=" * 80)
        
        # Authentication
        if not self.test_login():
            print("❌ Login failed - cannot continue tests")
            return False
        
        # Test 1: Basic SOCKS stats
        self.test_socks_stats_detailed()
        
        # Test 2: SOCKS start with real nodes (main test)
        self.test_socks_start_with_real_nodes()
        
        # Test 3: Node selection logic
        self.test_socks_start_node_selection_logic()
        
        # Test 4: Credentials generation
        self.test_socks_credentials_generation()
        
        # Test 5: Proxy file generation
        self.test_socks_proxy_file_generation()
        
        # Test 6: SOCKS stop and cleanup
        self.test_socks_stop_and_cleanup()
        
        # Test 7: Integration with main stats
        self.test_socks_integration_with_stats()
        
        # Final summary
        print("\n" + "=" * 80)
        print("🏁 SOCKS FOCUSED TESTING COMPLETE")
        print("=" * 80)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL SOCKS TESTS PASSED!")
            print("✅ SOCKS functionality is working correctly")
            print("✅ Russian user's issue may be resolved")
        else:
            print(f"\n⚠️ {self.tests_run - self.tests_passed} TESTS FAILED")
            print("❌ SOCKS functionality has issues")
            print("❌ Russian user's issue confirmed")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = SOCKSFocusedTester()
    success = tester.run_comprehensive_socks_focused_tests()
    sys.exit(0 if success else 1)