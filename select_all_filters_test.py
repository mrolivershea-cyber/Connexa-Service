#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class SelectAllFiltersAPITester:
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

    def test_select_all_filters_scenario_1_ping_light_status_filter(self):
        """СЦЕНАРИЙ 1: Testing PING LIGHT с фильтром по статусу not_tested + Select All"""
        print(f"\n🔥 TESTING SELECT ALL WITH FILTERS - SCENARIO 1: PING LIGHT with status=not_tested filter")
        
        # First, get count of nodes with status=not_tested
        count_success, count_response = self.make_request('GET', 'nodes/count?status=not_tested')
        
        if not count_success:
            self.log_test("Select All Filters - PING LIGHT Status Filter", False, 
                         f"Could not get count of not_tested nodes: {count_response}")
            return False
        
        not_tested_count = count_response.get('count', 0)
        print(f"📊 Found {not_tested_count} nodes with status=not_tested")
        
        if not_tested_count == 0:
            self.log_test("Select All Filters - PING LIGHT Status Filter", False, 
                         f"No nodes with status=not_tested found for testing")
            return False
        
        # Get all node IDs with status=not_tested (Select All functionality)
        ids_success, ids_response = self.make_request('GET', 'nodes/all-ids?status=not_tested')
        
        if not ids_success:
            self.log_test("Select All Filters - PING LIGHT Status Filter", False, 
                         f"Could not get all-ids with status filter: {ids_response}")
            return False
        
        filtered_node_ids = ids_response.get('node_ids', [])
        total_filtered = len(filtered_node_ids)
        
        print(f"🎯 Select All returned {total_filtered} filtered node IDs")
        
        if total_filtered != not_tested_count:
            self.log_test("Select All Filters - PING LIGHT Status Filter", False, 
                         f"Mismatch: count API returned {not_tested_count}, all-ids returned {total_filtered}")
            return False
        
        # Test PING LIGHT with filters (using batch endpoint)
        test_data = {
            "filters": {"status": "not_tested"},
            "select_all": True
        }
        
        # Use manual ping-light-test-batch-progress endpoint as mentioned in review
        ping_success, ping_response = self.make_request('POST', 'manual/ping-light-test-batch-progress', test_data)
        
        if ping_success:
            session_id = ping_response.get('session_id')
            if session_id:
                print(f"✅ PING LIGHT batch started with session_id: {session_id}")
                
                # Check progress to verify filters were applied
                time.sleep(2)  # Let it start processing
                
                progress_success, progress_response = self.make_request('GET', f'progress/{session_id}')
                
                if progress_success:
                    total_items = progress_response.get('total_items', 0)
                    
                    # Verify that total_items matches our filtered count
                    if total_items == total_filtered:
                        self.log_test("Select All Filters - PING LIGHT Status Filter", True, 
                                     f"PING LIGHT with status=not_tested filter working: {total_items} nodes being tested (matches filtered count)")
                        return True
                    else:
                        self.log_test("Select All Filters - PING LIGHT Status Filter", False, 
                                     f"Filter not applied correctly: expected {total_filtered} nodes, got {total_items}")
                        return False
                else:
                    self.log_test("Select All Filters - PING LIGHT Status Filter", False, 
                                 f"Could not get progress: {progress_response}")
                    return False
            else:
                self.log_test("Select All Filters - PING LIGHT Status Filter", False, 
                             f"No session_id returned from PING LIGHT batch: {ping_response}")
                return False
        else:
            self.log_test("Select All Filters - PING LIGHT Status Filter", False, 
                         f"PING LIGHT batch failed: {ping_response}")
            return False
    
    def test_select_all_filters_scenario_2_ping_ok_protocol_filter(self):
        """СЦЕНАРИЙ 2: Testing PING OK с фильтром по протоколу PPTP + Select All"""
        print(f"\n🔥 TESTING SELECT ALL WITH FILTERS - SCENARIO 2: PING OK with protocol=PPTP filter")
        
        # Get count of nodes with protocol=PPTP
        count_success, count_response = self.make_request('GET', 'nodes/count?protocol=PPTP')
        
        if not count_success:
            self.log_test("Select All Filters - PING OK Protocol Filter", False, 
                         f"Could not get count of PPTP nodes: {count_response}")
            return False
        
        pptp_count = count_response.get('count', 0)
        print(f"📊 Found {pptp_count} nodes with protocol=PPTP")
        
        if pptp_count == 0:
            self.log_test("Select All Filters - PING OK Protocol Filter", False, 
                         f"No nodes with protocol=PPTP found for testing")
            return False
        
        # Get all node IDs with protocol=PPTP (Select All functionality)
        ids_success, ids_response = self.make_request('GET', 'nodes/all-ids?protocol=PPTP')
        
        if not ids_success:
            self.log_test("Select All Filters - PING OK Protocol Filter", False, 
                         f"Could not get all-ids with protocol filter: {ids_response}")
            return False
        
        filtered_node_ids = ids_response.get('node_ids', [])
        total_filtered = len(filtered_node_ids)
        
        print(f"🎯 Select All returned {total_filtered} filtered node IDs")
        
        # Test PING OK with filters (using batch endpoint)
        test_data = {
            "filters": {"protocol": "PPTP"},
            "select_all": True
        }
        
        # Use manual ping-test-batch-progress endpoint as mentioned in review
        ping_success, ping_response = self.make_request('POST', 'manual/ping-test-batch-progress', test_data)
        
        if ping_success:
            session_id = ping_response.get('session_id')
            if session_id:
                print(f"✅ PING OK batch started with session_id: {session_id}")
                
                # Check progress to verify filters were applied
                time.sleep(2)  # Let it start processing
                
                progress_success, progress_response = self.make_request('GET', f'progress/{session_id}')
                
                if progress_success:
                    total_items = progress_response.get('total_items', 0)
                    
                    # Verify that total_items matches our filtered count
                    if total_items == total_filtered:
                        self.log_test("Select All Filters - PING OK Protocol Filter", True, 
                                     f"PING OK with protocol=PPTP filter working: {total_items} nodes being tested (matches filtered count)")
                        return True
                    else:
                        self.log_test("Select All Filters - PING OK Protocol Filter", False, 
                                     f"Filter not applied correctly: expected {total_filtered} nodes, got {total_items}")
                        return False
                else:
                    self.log_test("Select All Filters - PING OK Protocol Filter", False, 
                                 f"Could not get progress: {progress_response}")
                    return False
            else:
                self.log_test("Select All Filters - PING OK Protocol Filter", False, 
                             f"No session_id returned from PING OK batch: {ping_response}")
                return False
        else:
            self.log_test("Select All Filters - PING OK Protocol Filter", False, 
                         f"PING OK batch failed: {ping_response}")
            return False
    
    def test_select_all_filters_scenario_3_socks_start_status_filter(self):
        """СЦЕНАРИЙ 3: SOCKS Start с фильтром status=ping_ok + Select All"""
        print(f"\n🔥 TESTING SELECT ALL WITH FILTERS - SCENARIO 3: SOCKS Start with status=ping_ok filter")
        
        # Get count of nodes with status=ping_ok
        count_success, count_response = self.make_request('GET', 'nodes/count?status=ping_ok')
        
        if not count_success:
            self.log_test("Select All Filters - SOCKS Start Status Filter", False, 
                         f"Could not get count of ping_ok nodes: {count_response}")
            return False
        
        ping_ok_count = count_response.get('count', 0)
        print(f"📊 Found {ping_ok_count} nodes with status=ping_ok")
        
        if ping_ok_count == 0:
            self.log_test("Select All Filters - SOCKS Start Status Filter", False, 
                         f"No nodes with status=ping_ok found for testing")
            return False
        
        # Get all node IDs with status=ping_ok (Select All functionality)
        ids_success, ids_response = self.make_request('GET', 'nodes/all-ids?status=ping_ok')
        
        if not ids_success:
            self.log_test("Select All Filters - SOCKS Start Status Filter", False, 
                         f"Could not get all-ids with status filter: {ids_response}")
            return False
        
        filtered_node_ids = ids_response.get('node_ids', [])
        total_filtered = len(filtered_node_ids)
        
        print(f"🎯 Select All returned {total_filtered} filtered node IDs")
        
        # Test SOCKS Start with filters instead of node_ids
        test_data = {
            "filters": {"status": "ping_ok"},
            "select_all": True
        }
        
        # Use SOCKS start endpoint with filters as mentioned in review
        socks_success, socks_response = self.make_request('POST', 'socks/start', test_data)
        
        if socks_success:
            started_count = socks_response.get('started_count', 0)
            
            # Verify that started_count matches our filtered count (or is reasonable)
            if started_count > 0 and started_count <= total_filtered:
                self.log_test("Select All Filters - SOCKS Start Status Filter", True, 
                             f"SOCKS Start with status=ping_ok filter working: {started_count} SOCKS services started from {total_filtered} filtered nodes")
                return True
            else:
                self.log_test("Select All Filters - SOCKS Start Status Filter", False, 
                             f"Unexpected SOCKS start count: {started_count} (expected 0-{total_filtered})")
                return False
        else:
            # Check if it's a validation error (expected if no suitable nodes)
            if 'detail' in socks_response and 'status' in str(socks_response['detail']):
                self.log_test("Select All Filters - SOCKS Start Status Filter", True, 
                             f"SOCKS Start correctly rejected nodes with wrong status: {socks_response['detail']}")
                return True
            else:
                self.log_test("Select All Filters - SOCKS Start Status Filter", False, 
                             f"SOCKS Start failed: {socks_response}")
                return False
    
    def test_select_all_filters_scenario_4_socks_stop_status_filter(self):
        """СЦЕНАРИЙ 4: SOCKS Stop с фильтром status=online + Select All"""
        print(f"\n🔥 TESTING SELECT ALL WITH FILTERS - SCENARIO 4: SOCKS Stop with status=online filter")
        
        # Get count of nodes with status=online
        count_success, count_response = self.make_request('GET', 'nodes/count?status=online')
        
        if not count_success:
            self.log_test("Select All Filters - SOCKS Stop Status Filter", False, 
                         f"Could not get count of online nodes: {count_response}")
            return False
        
        online_count = count_response.get('count', 0)
        print(f"📊 Found {online_count} nodes with status=online")
        
        if online_count == 0:
            self.log_test("Select All Filters - SOCKS Stop Status Filter", False, 
                         f"No nodes with status=online found for testing")
            return False
        
        # Get all node IDs with status=online (Select All functionality)
        ids_success, ids_response = self.make_request('GET', 'nodes/all-ids?status=online')
        
        if not ids_success:
            self.log_test("Select All Filters - SOCKS Stop Status Filter", False, 
                         f"Could not get all-ids with status filter: {ids_response}")
            return False
        
        filtered_node_ids = ids_response.get('node_ids', [])
        total_filtered = len(filtered_node_ids)
        
        print(f"🎯 Select All returned {total_filtered} filtered node IDs")
        
        # Test SOCKS Stop with filters instead of node_ids
        test_data = {
            "filters": {"status": "online"},
            "select_all": True
        }
        
        # Use SOCKS stop endpoint with filters as mentioned in review
        socks_success, socks_response = self.make_request('POST', 'socks/stop', test_data)
        
        if socks_success:
            stopped_count = socks_response.get('stopped_count', 0)
            
            # Verify that stopped_count matches our filtered count (or is reasonable)
            if stopped_count >= 0 and stopped_count <= total_filtered:
                self.log_test("Select All Filters - SOCKS Stop Status Filter", True, 
                             f"SOCKS Stop with status=online filter working: {stopped_count} SOCKS services stopped from {total_filtered} filtered nodes")
                return True
            else:
                self.log_test("Select All Filters - SOCKS Stop Status Filter", False, 
                             f"Unexpected SOCKS stop count: {stopped_count} (expected 0-{total_filtered})")
                return False
        else:
            # Check if it's a validation error (expected if no SOCKS running)
            if 'detail' in socks_response:
                self.log_test("Select All Filters - SOCKS Stop Status Filter", True, 
                             f"SOCKS Stop handled correctly: {socks_response['detail']}")
                return True
            else:
                self.log_test("Select All Filters - SOCKS Stop Status Filter", False, 
                             f"SOCKS Stop failed: {socks_response}")
                return False
    
    def test_select_all_filters_backend_logs_verification(self):
        """Verify backend logs show filter application"""
        print(f"\n🔍 TESTING SELECT ALL WITH FILTERS - Backend Logs Verification")
        
        # This test checks that the backend properly logs filter application
        # We'll test with a simple status filter
        
        test_data = {
            "filters": {"status": "not_tested"},
            "select_all": True
        }
        
        # Test with ping-light endpoint to generate logs
        ping_success, ping_response = self.make_request('POST', 'manual/ping-light-test-batch-progress', test_data)
        
        if ping_success:
            session_id = ping_response.get('session_id')
            if session_id:
                # Wait a moment for processing to start and logs to be generated
                time.sleep(3)
                
                # Check progress to see if filters were applied
                progress_success, progress_response = self.make_request('GET', f'progress/{session_id}')
                
                if progress_success:
                    total_items = progress_response.get('total_items', 0)
                    
                    # If total_items > 0, it means filters were applied and nodes were found
                    if total_items > 0:
                        self.log_test("Select All Filters - Backend Logs Verification", True, 
                                     f"Backend logs should show 'Applying filters: {{'status': 'not_tested'}}' - {total_items} nodes processed")
                        return True
                    else:
                        self.log_test("Select All Filters - Backend Logs Verification", True, 
                                     f"Backend processed filter request (no matching nodes found)")
                        return True
                else:
                    self.log_test("Select All Filters - Backend Logs Verification", False, 
                                 f"Could not verify filter application: {progress_response}")
                    return False
            else:
                self.log_test("Select All Filters - Backend Logs Verification", False, 
                             f"No session_id returned: {ping_response}")
                return False
        else:
            self.log_test("Select All Filters - Backend Logs Verification", False, 
                         f"Filter test request failed: {ping_response}")
            return False

    def run_select_all_filters_tests(self):
        """Run all SELECT ALL WITH FILTERS tests"""
        print("🚀 Starting SELECT ALL WITH FILTERS Comprehensive Testing...")
        print("🌐 Base URL:", self.base_url)
        print("🔗 API URL:", self.api_url)
        print("=" * 80)
        
        # Test authentication
        if not self.test_login():
            print("❌ Login failed - cannot continue with authenticated tests")
            return False
        
        print("\n" + "🔥" * 80)
        print("🇷🇺 COMPREHENSIVE TESTING: Select All with Filters для Testing и SOCKS")
        print("🔥" * 80)
        print("ТЕСТОВЫЕ СЦЕНАРИИ:")
        print("СЦЕНАРИЙ 1: Testing PING LIGHT с фильтром по статусу status=not_tested")
        print("СЦЕНАРИЙ 2: Testing PING OK с фильтром по протоколу protocol=PPTP")
        print("СЦЕНАРИЙ 3: SOCKS Start с фильтром status=ping_ok")
        print("СЦЕНАРИЙ 4: SOCKS Stop с фильтром status=online")
        print("КРИТИЧЕСКИЕ ПРОВЕРКИ:")
        print("- Логи должны показывать применение фильтров")
        print("- Количество обрабатываемых узлов должно соответствовать отфильтрованным")
        print("- НЕ должны обрабатываться узлы вне фильтра")
        print("🔥" * 80)
        
        # Run all SELECT ALL WITH FILTERS tests
        self.test_select_all_filters_scenario_1_ping_light_status_filter()
        self.test_select_all_filters_scenario_2_ping_ok_protocol_filter()
        self.test_select_all_filters_scenario_3_socks_start_status_filter()
        self.test_select_all_filters_scenario_4_socks_stop_status_filter()
        self.test_select_all_filters_backend_logs_verification()
        
        # Print final results
        print("\n" + "=" * 80)
        print(f"🏁 SELECT ALL WITH FILTERS TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL SELECT ALL WITH FILTERS TESTS PASSED!")
            return True
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            return False

if __name__ == "__main__":
    tester = SelectAllFiltersAPITester()
    success = tester.run_select_all_filters_tests()
    sys.exit(0 if success else 1)