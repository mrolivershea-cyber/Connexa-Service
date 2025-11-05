#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class BulkDeleteTester:
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

    def test_bulk_delete_scenario_1_select_all_delete_all(self):
        """СЦЕНАРИЙ 1 - Массовое удаление всех узлов: Test Select All + Delete with delete_all=true"""
        print(f"\n🔥 TESTING BULK DELETE - SCENARIO 1: Select All + Delete All Nodes")
        
        # First, create some test nodes to delete
        test_nodes_data = []
        for i in range(10):
            test_nodes_data.append({
                "ip": f"203.0.113.{i+10}",
                "login": f"bulktest{i}",
                "password": f"bulkpass{i}",
                "protocol": "pptp",
                "status": "not_tested"
            })
        
        # Create the test nodes
        created_node_ids = []
        for node_data in test_nodes_data:
            success, response = self.make_request('POST', 'nodes', node_data)
            if success and 'id' in response:
                created_node_ids.append(response['id'])
        
        if len(created_node_ids) < 10:
            self.log_test("Bulk Delete Scenario 1 - Setup", False, 
                         f"❌ Could not create test nodes: only {len(created_node_ids)}/10 created")
            return False
        
        print(f"✅ Created {len(created_node_ids)} test nodes for bulk delete test")
        
        # Test bulk delete with delete_all=true (simulating Select All scenario)
        delete_data = {
            "delete_all": True
        }
        
        success, response = self.make_request('DELETE', 'nodes/bulk', delete_data)
        
        if success and 'deleted_count' in response:
            deleted_count = response['deleted_count']
            print(f"📊 Bulk delete response: {deleted_count} nodes deleted")
            
            # Verify that our test nodes were actually deleted
            verification_success = True
            deleted_test_nodes = 0
            for node_id in created_node_ids:
                check_success, check_response = self.make_request('GET', f'nodes/{node_id}', expected_status=404)
                if check_success:  # 404 means node was deleted
                    deleted_test_nodes += 1
                else:
                    verification_success = False
                    print(f"❌ Node {node_id} still exists after bulk delete")
            
            if verification_success and deleted_test_nodes == len(created_node_ids):
                self.log_test("Bulk Delete Scenario 1 - Select All Delete All", True, 
                             f"✅ Bulk delete with delete_all=true working: {deleted_count} total nodes deleted, all {deleted_test_nodes} test nodes verified deleted")
                return True
            else:
                self.log_test("Bulk Delete Scenario 1 - Select All Delete All", False, 
                             f"❌ Bulk delete verification failed: deleted_count={deleted_count}, test_nodes_deleted={deleted_test_nodes}/{len(created_node_ids)}")
                return False
        else:
            self.log_test("Bulk Delete Scenario 1 - Select All Delete All", False, 
                         f"❌ Bulk delete failed: {response}")
            return False
    
    def test_bulk_delete_scenario_2_filtered_delete(self):
        """СЦЕНАРИЙ 2 - Массовое удаление с фильтрами: Test filtered bulk delete (status=not_tested)"""
        print(f"\n🔥 TESTING BULK DELETE - SCENARIO 2: Filtered Bulk Delete")
        
        # Create test nodes with different statuses
        test_nodes_data = [
            {"ip": "203.0.114.1", "login": "filtertest1", "password": "pass1", "protocol": "pptp", "status": "not_tested"},
            {"ip": "203.0.114.2", "login": "filtertest2", "password": "pass2", "protocol": "pptp", "status": "not_tested"},
            {"ip": "203.0.114.3", "login": "filtertest3", "password": "pass3", "protocol": "pptp", "status": "ping_ok"},
            {"ip": "203.0.114.4", "login": "filtertest4", "password": "pass4", "protocol": "pptp", "status": "not_tested"},
            {"ip": "203.0.114.5", "login": "filtertest5", "password": "pass5", "protocol": "socks", "status": "not_tested"}
        ]
        
        # Create the test nodes
        created_node_ids = []
        for node_data in test_nodes_data:
            success, response = self.make_request('POST', 'nodes', node_data)
            if success and 'id' in response:
                created_node_ids.append(response['id'])
        
        if len(created_node_ids) < 5:
            self.log_test("Bulk Delete Scenario 2 - Setup", False, 
                         f"❌ Could not create test nodes: only {len(created_node_ids)}/5 created")
            return False
        
        print(f"✅ Created {len(created_node_ids)} test nodes with mixed statuses")
        
        # Test filtered bulk delete (status=not_tested)
        delete_data = {
            "status": "not_tested"
        }
        
        success, response = self.make_request('DELETE', 'nodes/bulk', delete_data)
        
        if success and 'deleted_count' in response:
            deleted_count = response['deleted_count']
            print(f"📊 Filtered delete response: {deleted_count} not_tested nodes deleted")
            
            # Should delete 4 nodes (not_tested) but keep 1 node (ping_ok)
            if deleted_count >= 4:
                # Verify that ping_ok node still exists
                ping_ok_node_success, ping_ok_response = self.make_request('GET', 'nodes?ip=203.0.114.3')
                
                if ping_ok_node_success and 'nodes' in ping_ok_response and ping_ok_response['nodes']:
                    node = ping_ok_response['nodes'][0]
                    if node.get('status') == 'ping_ok':
                        self.log_test("Bulk Delete Scenario 2 - Filtered Delete", True, 
                                     f"✅ Filtered bulk delete working: {deleted_count} not_tested nodes deleted, ping_ok node preserved")
                        return True
                    else:
                        self.log_test("Bulk Delete Scenario 2 - Filtered Delete", False, 
                                     f"❌ ping_ok node status changed: {node.get('status')}")
                        return False
                else:
                    self.log_test("Bulk Delete Scenario 2 - Filtered Delete", False, 
                                 f"❌ ping_ok node was incorrectly deleted")
                    return False
            else:
                self.log_test("Bulk Delete Scenario 2 - Filtered Delete", False, 
                             f"❌ Expected at least 4 deletions, got {deleted_count}")
                return False
        else:
            self.log_test("Bulk Delete Scenario 2 - Filtered Delete", False, 
                         f"❌ Filtered bulk delete failed: {response}")
            return False
    
    def test_bulk_delete_scenario_3_individual_selection_delete(self):
        """СЦЕНАРИЙ 3 - Обычное удаление выбранных: Test individual node selection delete via /nodes endpoint"""
        print(f"\n🔥 TESTING BULK DELETE - SCENARIO 3: Individual Selection Delete")
        
        # Create test nodes for individual selection
        test_nodes_data = [
            {"ip": "203.0.115.1", "login": "individual1", "password": "pass1", "protocol": "pptp"},
            {"ip": "203.0.115.2", "login": "individual2", "password": "pass2", "protocol": "pptp"},
            {"ip": "203.0.115.3", "login": "individual3", "password": "pass3", "protocol": "pptp"},
            {"ip": "203.0.115.4", "login": "individual4", "password": "pass4", "protocol": "pptp"}
        ]
        
        # Create the test nodes
        created_node_ids = []
        for node_data in test_nodes_data:
            success, response = self.make_request('POST', 'nodes', node_data)
            if success and 'id' in response:
                created_node_ids.append(response['id'])
        
        if len(created_node_ids) < 4:
            self.log_test("Bulk Delete Scenario 3 - Setup", False, 
                         f"❌ Could not create test nodes: only {len(created_node_ids)}/4 created")
            return False
        
        print(f"✅ Created {len(created_node_ids)} test nodes for individual selection")
        
        # Select 2 nodes for deletion (simulating individual selection)
        selected_node_ids = created_node_ids[:2]
        remaining_node_ids = created_node_ids[2:]
        
        print(f"📋 Selected {len(selected_node_ids)} nodes for deletion: {selected_node_ids}")
        print(f"📋 Expecting {len(remaining_node_ids)} nodes to remain: {remaining_node_ids}")
        
        # Test individual selection delete via /nodes endpoint
        delete_data = {
            "node_ids": selected_node_ids
        }
        
        success, response = self.make_request('DELETE', 'nodes', delete_data)
        
        if success and 'message' in response:
            print(f"📊 Individual delete response: {response['message']}")
            
            # Verify selected nodes were deleted
            deleted_verification = True
            for node_id in selected_node_ids:
                check_success, check_response = self.make_request('GET', f'nodes/{node_id}', expected_status=404)
                if not check_success:
                    deleted_verification = False
                    print(f"❌ Selected node {node_id} was not deleted")
                    break
            
            # Verify remaining nodes still exist
            remaining_verification = True
            for node_id in remaining_node_ids:
                check_success, check_response = self.make_request('GET', f'nodes/{node_id}')
                if not check_success:
                    remaining_verification = False
                    print(f"❌ Remaining node {node_id} was incorrectly deleted")
                    break
            
            if deleted_verification and remaining_verification:
                self.log_test("Bulk Delete Scenario 3 - Individual Selection Delete", True, 
                             f"✅ Individual selection delete working: {len(selected_node_ids)} selected nodes deleted, {len(remaining_node_ids)} remaining nodes preserved")
                return True
            else:
                self.log_test("Bulk Delete Scenario 3 - Individual Selection Delete", False, 
                             f"❌ Verification failed: deleted_ok={deleted_verification}, remaining_ok={remaining_verification}")
                return False
        else:
            self.log_test("Bulk Delete Scenario 3 - Individual Selection Delete", False, 
                         f"❌ Individual selection delete failed: {response}")
            return False
    
    def test_bulk_delete_error_handling_validation(self):
        """Test bulk delete error handling and validation (no filters + no delete_all)"""
        print(f"\n🔥 TESTING BULK DELETE - ERROR HANDLING: Validation Requirements")
        
        # Test 1: No filters and no delete_all (should fail)
        delete_data = {}
        
        success, response = self.make_request('DELETE', 'nodes/bulk', delete_data, expected_status=400)
        
        if success and 'detail' in response:
            error_message = response['detail']
            print(f"📊 Validation error message: {error_message}")
            if 'Must specify filters' in error_message or 'delete_all=true' in error_message:
                self.log_test("Bulk Delete Error Handling - No Filters Validation", True, 
                             f"✅ Validation working: correctly rejected request without filters or delete_all")
                return True
            else:
                self.log_test("Bulk Delete Error Handling - No Filters Validation", False, 
                             f"❌ Wrong error message: {error_message}")
                return False
        else:
            self.log_test("Bulk Delete Error Handling - No Filters Validation", False, 
                         f"❌ Expected 400 error, got: {response}")
            return False
    
    def test_bulk_delete_object_object_error_fix(self):
        """Test that the '[object Object]' error is fixed in bulk delete operations"""
        print(f"\n🔥 TESTING BULK DELETE - [object Object] ERROR FIX")
        
        # Create a test node
        test_node = {
            "ip": "203.0.116.1",
            "login": "errortest",
            "password": "errorpass",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes', test_node)
        if not success:
            self.log_test("Bulk Delete Object Error Fix - Setup", False, 
                         f"❌ Could not create test node: {response}")
            return False
        
        print(f"✅ Created test node for error fix verification")
        
        # Test bulk delete that should work (with proper filters)
        delete_data = {
            "status": "not_tested"
        }
        
        success, response = self.make_request('DELETE', 'nodes/bulk', delete_data)
        
        if success:
            print(f"📊 Bulk delete response: {response}")
            # Check that response is properly formatted JSON (not "[object Object]")
            if isinstance(response, dict) and 'message' in response:
                message = response['message']
                if '[object Object]' not in str(message) and 'deleted' in message.lower():
                    self.log_test("Bulk Delete Object Error Fix", True, 
                                 f"✅ [object Object] error fixed: proper response format returned: {message}")
                    return True
                else:
                    self.log_test("Bulk Delete Object Error Fix", False, 
                                 f"❌ Response format issue: {message}")
                    return False
            else:
                self.log_test("Bulk Delete Object Error Fix", False, 
                             f"❌ Response not properly formatted: {response}")
                return False
        else:
            self.log_test("Bulk Delete Object Error Fix", False, 
                         f"❌ Bulk delete failed: {response}")
            return False

    def run_bulk_delete_tests(self):
        """Run all bulk delete tests"""
        print("🚀 Starting Bulk Delete Testing Suite")
        print("=" * 60)
        print("🇷🇺 ТЕСТИРОВАНИЕ ИСПРАВЛЕННОГО МАССОВОГО УДАЛЕНИЯ")
        print("ПРОБЛЕМА БЫЛА: '[object Object]' ошибка при попытке массового удаления")
        print("=" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Run all bulk delete scenarios
        print("\n🔥 RUNNING ALL BULK DELETE SCENARIOS:")
        
        scenario_1_result = self.test_bulk_delete_scenario_1_select_all_delete_all()
        scenario_2_result = self.test_bulk_delete_scenario_2_filtered_delete()
        scenario_3_result = self.test_bulk_delete_scenario_3_individual_selection_delete()
        error_handling_result = self.test_bulk_delete_error_handling_validation()
        object_error_fix_result = self.test_bulk_delete_object_object_error_fix()
        
        # Summary
        total_scenarios = 5
        passed_scenarios = sum([scenario_1_result, scenario_2_result, scenario_3_result, 
                               error_handling_result, object_error_fix_result])
        
        print("\n" + "=" * 60)
        print(f"🏁 BULK DELETE TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        print(f"🎯 Scenarios: {passed_scenarios}/{total_scenarios} scenarios passed")
        
        if passed_scenarios == total_scenarios:
            print("✅ ALL BULK DELETE SCENARIOS PASSED!")
            print("✅ Select All + Delete All: WORKING")
            print("✅ Filtered Delete (status=not_tested): WORKING") 
            print("✅ Individual Selection Delete: WORKING")
            print("✅ Error Handling & Validation: WORKING")
            print("✅ [object Object] Error Fix: WORKING")
            return True
        else:
            print(f"❌ {total_scenarios - passed_scenarios} scenarios failed")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
            return False

if __name__ == "__main__":
    tester = BulkDeleteTester()
    success = tester.run_bulk_delete_tests()
    sys.exit(0 if success else 1)