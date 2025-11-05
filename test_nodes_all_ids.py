#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class NodesAllIdsAPITester:
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

    def test_nodes_all_ids_authentication(self):
        """Test that /api/nodes/all-ids requires authentication"""
        # Save current token
        original_token = self.token
        
        # Clear token to test unauthenticated access
        self.token = None
        
        success, response = self.make_request('GET', 'nodes/all-ids')
        
        # Restore token
        self.token = original_token
        
        # Check if authentication is required (should fail without token)
        if not success and 'detail' in response and 'authenticated' in response['detail'].lower():
            self.log_test("Nodes All IDs - Authentication Required", True, f"✅ Endpoint correctly requires authentication: {response['detail']}")
            return True
        else:
            self.log_test("Nodes All IDs - Authentication Required", False, f"❌ Expected authentication error, got: {response}")
            return False

    def test_nodes_all_ids_endpoint(self):
        """Test the new /api/nodes/all-ids endpoint for Select All functionality"""
        print("\n🔍 TESTING NEW /api/nodes/all-ids ENDPOINT")
        
        # Test 1: Basic functionality without filters
        success1, response1 = self.make_request('GET', 'nodes/all-ids')
        
        if not success1:
            self.log_test("Nodes All IDs - Basic", False, f"❌ Basic request failed: {response1}")
            return False
        
        # Verify response structure
        if not ('node_ids' in response1 and 'total_count' in response1):
            self.log_test("Nodes All IDs - Basic", False, f"❌ Response missing required fields. Got: {list(response1.keys())}")
            return False
        
        node_ids = response1['node_ids']
        total_count = response1['total_count']
        
        if not isinstance(node_ids, list):
            self.log_test("Nodes All IDs - Basic", False, f"❌ node_ids should be a list, got: {type(node_ids)}")
            return False
        
        if len(node_ids) != total_count:
            self.log_test("Nodes All IDs - Basic", False, f"❌ node_ids length ({len(node_ids)}) != total_count ({total_count})")
            return False
        
        self.log_test("Nodes All IDs - Basic", True, f"✅ Basic functionality works: {total_count} node IDs returned")
        
        # Test 2: Compare with /api/nodes endpoint counts
        success2, response2 = self.make_request('GET', 'nodes')
        
        if success2 and 'total' in response2:
            nodes_total = response2['total']
            if total_count == nodes_total:
                self.log_test("Nodes All IDs - Count Consistency", True, f"✅ Counts match: /api/nodes total={nodes_total}, /api/nodes/all-ids total_count={total_count}")
            else:
                self.log_test("Nodes All IDs - Count Consistency", False, f"❌ Count mismatch: /api/nodes total={nodes_total}, /api/nodes/all-ids total_count={total_count}")
                return False
        else:
            self.log_test("Nodes All IDs - Count Consistency", False, f"❌ Could not get /api/nodes for comparison: {response2}")
            return False
        
        # Test 3: Test with filters - status filter
        success3, response3 = self.make_request('GET', 'nodes/all-ids', {'status': 'not_tested'})
        
        if success3 and 'node_ids' in response3 and 'total_count' in response3:
            filtered_count = response3['total_count']
            
            # Compare with filtered /api/nodes
            success4, response4 = self.make_request('GET', 'nodes', {'status': 'not_tested'})
            
            if success4 and 'total' in response4:
                nodes_filtered_total = response4['total']
                if filtered_count == nodes_filtered_total:
                    self.log_test("Nodes All IDs - Status Filter", True, f"✅ Status filter works: not_tested nodes = {filtered_count}")
                else:
                    self.log_test("Nodes All IDs - Status Filter", False, f"❌ Status filter count mismatch: all-ids={filtered_count}, nodes={nodes_filtered_total}")
                    return False
            else:
                self.log_test("Nodes All IDs - Status Filter", False, f"❌ Could not get filtered /api/nodes for comparison")
                return False
        else:
            self.log_test("Nodes All IDs - Status Filter", False, f"❌ Status filter request failed: {response3}")
            return False
        
        # Test 4: Test with multiple filters
        success5, response5 = self.make_request('GET', 'nodes/all-ids', {'protocol': 'pptp', 'status': 'not_tested'})
        
        if success5 and 'node_ids' in response5 and 'total_count' in response5:
            multi_filtered_count = response5['total_count']
            
            # Compare with multi-filtered /api/nodes
            success6, response6 = self.make_request('GET', 'nodes', {'protocol': 'pptp', 'status': 'not_tested'})
            
            if success6 and 'total' in response6:
                nodes_multi_filtered_total = response6['total']
                if multi_filtered_count == nodes_multi_filtered_total:
                    self.log_test("Nodes All IDs - Multiple Filters", True, f"✅ Multiple filters work: pptp+not_tested nodes = {multi_filtered_count}")
                else:
                    self.log_test("Nodes All IDs - Multiple Filters", False, f"❌ Multiple filters count mismatch: all-ids={multi_filtered_count}, nodes={nodes_multi_filtered_total}")
                    return False
            else:
                self.log_test("Nodes All IDs - Multiple Filters", False, f"❌ Could not get multi-filtered /api/nodes for comparison")
                return False
        else:
            self.log_test("Nodes All IDs - Multiple Filters", False, f"❌ Multiple filters request failed: {response5}")
            return False
        
        # Test 5: Test with only_online filter
        success7, response7 = self.make_request('GET', 'nodes/all-ids', {'only_online': True})
        
        if success7 and 'node_ids' in response7 and 'total_count' in response7:
            online_count = response7['total_count']
            
            # Compare with only_online /api/nodes
            success8, response8 = self.make_request('GET', 'nodes', {'only_online': True})
            
            if success8 and 'total' in response8:
                nodes_online_total = response8['total']
                if online_count == nodes_online_total:
                    self.log_test("Nodes All IDs - Only Online Filter", True, f"✅ only_online filter works: online nodes = {online_count}")
                else:
                    self.log_test("Nodes All IDs - Only Online Filter", False, f"❌ only_online filter count mismatch: all-ids={online_count}, nodes={nodes_online_total}")
                    return False
            else:
                self.log_test("Nodes All IDs - Only Online Filter", False, f"❌ Could not get only_online /api/nodes for comparison")
                return False
        else:
            self.log_test("Nodes All IDs - Only Online Filter", False, f"❌ only_online filter request failed: {response7}")
            return False
        
        # Test 6: Test with text filters (ip, provider, country, state, city, zipcode, login, comment)
        success9, response9 = self.make_request('GET', 'nodes/all-ids', {'country': 'United States'})
        
        if success9 and 'node_ids' in response9 and 'total_count' in response9:
            country_count = response9['total_count']
            
            # Compare with country filtered /api/nodes
            success10, response10 = self.make_request('GET', 'nodes', {'country': 'United States'})
            
            if success10 and 'total' in response10:
                nodes_country_total = response10['total']
                if country_count == nodes_country_total:
                    self.log_test("Nodes All IDs - Text Filters", True, f"✅ Text filters work: United States nodes = {country_count}")
                else:
                    self.log_test("Nodes All IDs - Text Filters", False, f"❌ Text filter count mismatch: all-ids={country_count}, nodes={nodes_country_total}")
                    return False
            else:
                self.log_test("Nodes All IDs - Text Filters", False, f"❌ Could not get country filtered /api/nodes for comparison")
                return False
        else:
            self.log_test("Nodes All IDs - Text Filters", False, f"❌ Text filter request failed: {response9}")
            return False
        
        print(f"📊 ALL-IDS ENDPOINT TEST SUMMARY:")
        print(f"   Total nodes in database: {total_count}")
        print(f"   not_tested nodes: {filtered_count}")
        print(f"   pptp+not_tested nodes: {multi_filtered_count}")
        print(f"   online nodes: {online_count}")
        print(f"   United States nodes: {country_count}")
        
        return True

    def run_tests(self):
        """Run the /api/nodes/all-ids endpoint tests"""
        print(f"\n{'='*80}")
        print(f"🚀 TESTING NEW /api/nodes/all-ids ENDPOINT")
        print(f"{'='*80}")
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")
        
        # Test authentication first
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Test authentication requirement
        self.test_nodes_all_ids_authentication()
        
        # Test the endpoint functionality
        self.test_nodes_all_ids_endpoint()
        
        # Print final results
        print(f"\n{'='*80}")
        print(f"🏁 TEST RESULTS SUMMARY")
        print(f"{'='*80}")
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print("❌ SOME TESTS FAILED!")
            return False

def main():
    tester = NodesAllIdsAPITester()
    success = tester.run_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())