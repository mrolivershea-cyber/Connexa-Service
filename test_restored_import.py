#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class RestoreImportTester:
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

    def test_scenario_1_import_with_duplicates(self):
        """СЦЕНАРИЙ 1 - Импорт с дубликатами: Test import with duplicates and verify correct reporting"""
        print(f"\n🇷🇺 TESTING SCENARIO 1: Import with Duplicates - Smart Duplicate Checking")
        
        # First, import some initial nodes
        initial_data = {
            "data": """5.78.100.1:admin:admin
5.78.100.2:user1:pass1
5.78.100.3:user2:pass2""",
            "protocol": "pptp"
        }
        
        success1, response1 = self.make_request('POST', 'nodes/import', initial_data)
        
        if not success1:
            self.log_test("Scenario 1 - Initial Import", False, f"Initial import failed: {response1}")
            return False
        
        # Now import with some duplicates and some new nodes
        duplicate_data = {
            "data": """5.78.100.1:admin:admin
5.78.100.2:user1:pass1
5.78.100.4:user3:pass3
5.78.100.5:user4:pass4""",
            "protocol": "pptp"
        }
        
        success2, response2 = self.make_request('POST', 'nodes/import', duplicate_data)
        
        if success2 and 'report' in response2:
            report = response2['report']
            added = report.get('added', 0)
            skipped = report.get('skipped_duplicates', 0)
            
            # Should have 2 new nodes added and 2 duplicates skipped
            if added >= 2 and skipped >= 2:
                self.log_test("Scenario 1 - Import with Duplicates", True, 
                             f"✅ Smart duplicate checking working: {added} added, {skipped} skipped (exact IP+login+password duplicates)")
                return True
            else:
                self.log_test("Scenario 1 - Import with Duplicates", False, 
                             f"❌ Expected 2 added + 2 skipped, got {added} added + {skipped} skipped")
                return False
        else:
            self.log_test("Scenario 1 - Import with Duplicates", False, f"Duplicate import failed: {response2}")
            return False
    
    def test_scenario_2_bulk_deletion(self):
        """СЦЕНАРИЙ 2 - Массовое удаление: Test bulk deletion endpoints"""
        print(f"\n🇷🇺 TESTING SCENARIO 2: Bulk Deletion - /api/nodes/bulk and /api/nodes/batch endpoints")
        
        # First, create some test nodes for deletion
        test_data = {
            "data": """10.0.200.1:deluser1:delpass1
10.0.200.2:deluser2:delpass2
10.0.200.3:deluser3:delpass3""",
            "protocol": "pptp"
        }
        
        success1, response1 = self.make_request('POST', 'nodes/import', test_data)
        
        if not success1:
            self.log_test("Scenario 2 - Setup Test Nodes", False, f"Failed to create test nodes: {response1}")
            return False
        
        # Test /api/nodes/bulk endpoint (delete by filters)
        bulk_delete_params = {
            "search": "deluser"  # This should match all our test nodes
        }
        
        # For DELETE with query params, we need to use a different approach
        url = f"{self.api_url}/nodes/bulk"
        headers = self.headers.copy()
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            response = requests.delete(url, headers=headers, params=bulk_delete_params)
            success2 = response.status_code == 200
            try:
                response2 = response.json()
            except:
                response2 = {"text": response.text, "status_code": response.status_code}
        except Exception as e:
            success2 = False
            response2 = {"error": str(e)}
        
        if success2 and 'deleted_count' in response2:
            deleted_count = response2['deleted_count']
            
            if deleted_count >= 3:
                self.log_test("Scenario 2 - Bulk Delete by Filter", True, 
                             f"✅ /api/nodes/bulk endpoint working: {deleted_count} nodes deleted by filter")
                
                # Test /api/nodes/batch endpoint (delete by IDs)
                # First create more test nodes and get their IDs
                batch_test_data = {
                    "data": """10.0.201.1:batchuser1:batchpass1
10.0.201.2:batchuser2:batchpass2""",
                    "protocol": "pptp"
                }
                
                success3, response3 = self.make_request('POST', 'nodes/import', batch_test_data)
                
                if success3:
                    # Get the node IDs
                    nodes_success, nodes_response = self.make_request('GET', 'nodes?login=batchuser1')
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node_id1 = nodes_response['nodes'][0]['id']
                        
                        nodes_success2, nodes_response2 = self.make_request('GET', 'nodes?login=batchuser2')
                        if nodes_success2 and 'nodes' in nodes_response2 and nodes_response2['nodes']:
                            node_id2 = nodes_response2['nodes'][0]['id']
                            
                            # Test batch deletion by IDs
                            batch_delete_data = {
                                "node_ids": [node_id1, node_id2]
                            }
                            
                            success4, response4 = self.make_request('DELETE', 'nodes/batch', batch_delete_data)
                            
                            if success4 and 'deleted_count' in response4:
                                batch_deleted = response4['deleted_count']
                                
                                if batch_deleted >= 2:
                                    self.log_test("Scenario 2 - Batch Delete by IDs", True, 
                                                 f"✅ /api/nodes/batch endpoint working: {batch_deleted} nodes deleted by IDs")
                                    return True
                                else:
                                    self.log_test("Scenario 2 - Batch Delete by IDs", False, 
                                                 f"❌ Expected 2 nodes deleted, got {batch_deleted}")
                                    return False
                            else:
                                self.log_test("Scenario 2 - Batch Delete by IDs", False, f"Batch delete failed: {response4}")
                                return False
                
                self.log_test("Scenario 2 - Batch Delete Setup", False, "Could not setup batch delete test")
                return False
            else:
                self.log_test("Scenario 2 - Bulk Delete by Filter", False, 
                             f"❌ Expected at least 3 nodes deleted, got {deleted_count}")
                return False
        else:
            self.log_test("Scenario 2 - Bulk Delete by Filter", False, f"Bulk delete failed: {response2}")
            return False
    
    def test_scenario_3_chunked_import_final_report(self):
        """СЦЕНАРИЙ 3 - Chunked импорт отчёты: Test large file import with detailed final_report"""
        print(f"\n🇷🇺 TESTING SCENARIO 3: Chunked Import Final Report - Detailed Statistics")
        
        # Create a large file to trigger chunked import
        large_data_lines = []
        for i in range(3000):  # Smaller for faster testing
            large_data_lines.append(f"172.20.{(i//256)+1}.{i%256}:chunkuser{i}:chunkpass{i}")
        
        # Add some duplicates to test reporting
        large_data_lines.append("172.20.1.0:chunkuser0:chunkpass0")  # Duplicate
        large_data_lines.append("172.20.1.1:chunkuser1:chunkpass1")  # Duplicate
        
        large_data = "\n".join(large_data_lines)
        data_size = len(large_data.encode('utf-8'))
        
        import_data = {
            "data": large_data,
            "protocol": "pptp"
        }
        
        # Test chunked import
        success, response = self.make_request('POST', 'nodes/import-chunked', import_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            total_chunks = response.get('total_chunks', 0)
            
            # Wait for processing to complete
            max_wait = 60  # Maximum 60 seconds
            wait_time = 0
            
            while wait_time < max_wait:
                progress_success, progress_response = self.make_request('GET', f'import/progress/{session_id}')
                
                if progress_success:
                    status = progress_response.get('status', 'unknown')
                    
                    if status == 'completed':
                        # Check for final_report with detailed statistics
                        final_report = progress_response.get('final_report', {})
                        
                        if final_report:
                            required_fields = ['total_processed', 'added', 'skipped_duplicates', 'replaced_old', 'format_errors', 'success_rate']
                            missing_fields = [field for field in required_fields if field not in final_report]
                            
                            if not missing_fields:
                                success_rate = final_report.get('success_rate', 0)
                                added = final_report.get('added', 0)
                                skipped = final_report.get('skipped_duplicates', 0)
                                
                                self.log_test("Scenario 3 - Chunked Import Final Report", True, 
                                             f"✅ Detailed final_report working: {data_size/1024:.1f}KB file, {total_chunks} chunks, {added} added, {skipped} skipped, {success_rate}% success rate")
                                return True
                            else:
                                self.log_test("Scenario 3 - Chunked Import Final Report", False, 
                                             f"❌ Missing final_report fields: {missing_fields}")
                                return False
                        else:
                            self.log_test("Scenario 3 - Chunked Import Final Report", False, 
                                         "❌ No final_report found in completed import")
                            return False
                    elif status == 'failed':
                        self.log_test("Scenario 3 - Chunked Import Final Report", False, 
                                     f"❌ Import failed: {progress_response.get('current_operation', 'unknown error')}")
                        return False
                
                time.sleep(2)
                wait_time += 2
            
            self.log_test("Scenario 3 - Chunked Import Final Report", False, 
                         f"❌ Import did not complete within {max_wait} seconds")
            return False
        else:
            self.log_test("Scenario 3 - Chunked Import Final Report", False, f"Chunked import failed to start: {response}")
            return False

    def run_tests(self):
        """Run the restored import functionality tests"""
        print("🇷🇺 RUSSIAN USER REVIEW REQUEST - RESTORED IMPORT FUNCTIONALITY TESTING")
        print("=" * 80)
        
        # Login first
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Run the specific scenarios
        self.test_scenario_1_import_with_duplicates()
        self.test_scenario_2_bulk_deletion()
        self.test_scenario_3_chunked_import_final_report()
        
        # Print final results
        print("\n" + "=" * 80)
        print(f"🏁 TESTING COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL TESTS PASSED!")
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = RestoreImportTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)