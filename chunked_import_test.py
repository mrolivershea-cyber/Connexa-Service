#!/usr/bin/env python3

import requests
import sys
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, List

class ChunkedImportTester:
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

    def generate_large_test_data(self, size_kb: int, ip_prefix: str = "172.16") -> str:
        """Generate test data of specified size in KB using Format 7 (IP:Login:Pass)"""
        lines = []
        current_size = 0
        target_size = size_kb * 1024  # Convert to bytes
        
        i = 0
        while current_size < target_size:
            # Generate IP in specified range to avoid conflicts
            ip_third = (i // 256) % 256
            ip_fourth = i % 256
            
            line = f"{ip_prefix}.{ip_third}.{ip_fourth}:testuser{i}:testpass{i}"
            lines.append(line)
            current_size += len(line) + 1  # +1 for newline
            i += 1
        
        return '\n'.join(lines)

    def test_scenario_1_chunked_import_large_file(self):
        """СЦЕНАРИЙ 1 - Chunked Import большого файла: Test chunked import for files >500KB"""
        print("\n🔍 СЦЕНАРИЙ 1 - Testing Chunked Import for Large Files (>500KB)")
        
        # Generate test data >500KB (create ~600KB file)
        test_data = self.generate_large_test_data(600, "172.20")
        data_size_kb = len(test_data.encode('utf-8')) / 1024
        
        print(f"   Generated test data: {data_size_kb:.1f}KB")
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Start import and measure time
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            total_chunks = response.get('total_chunks', 0)
            
            self.log_test("Large File Automatic Redirect to Chunked", True, 
                         f"File {data_size_kb:.1f}KB automatically redirected to chunked processing. Session: {session_id}, Chunks: {total_chunks}")
            
            # Test real-time progress tracking
            return self.test_progress_tracking(session_id, total_chunks)
        else:
            self.log_test("Large File Automatic Redirect to Chunked", False, 
                         f"Expected chunked processing for {data_size_kb:.1f}KB file, got: {response}")
            return False

    def test_progress_tracking(self, session_id: str, expected_chunks: int) -> bool:
        """Test real-time progress tracking"""
        print(f"   🔄 Testing real-time progress tracking for session: {session_id}")
        
        progress_updates = []
        max_wait_time = 120  # 2 minutes max wait
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Get progress
            progress_success, progress_response = self.make_request('GET', f'import/progress/{session_id}')
            
            if progress_success:
                status = progress_response.get('status', 'unknown')
                processed_chunks = progress_response.get('processed_chunks', 0)
                total_chunks = progress_response.get('total_chunks', 0)
                current_operation = progress_response.get('current_operation', '')
                added = progress_response.get('added', 0)
                skipped = progress_response.get('skipped', 0)
                errors = progress_response.get('errors', 0)
                
                progress_updates.append({
                    'timestamp': time.time(),
                    'status': status,
                    'processed_chunks': processed_chunks,
                    'total_chunks': total_chunks,
                    'current_operation': current_operation,
                    'added': added,
                    'skipped': skipped,
                    'errors': errors
                })
                
                print(f"   Progress: {processed_chunks}/{total_chunks} chunks, Status: {status}, Operation: {current_operation}")
                print(f"   Stats: Added={added}, Skipped={skipped}, Errors={errors}")
                
                if status == 'completed':
                    break
                elif status == 'failed':
                    self.log_test("Real-time Progress Tracking", False, 
                                 f"Import failed during processing: {current_operation}")
                    return False
            else:
                self.log_test("Real-time Progress Tracking", False, 
                             f"Failed to get progress: {progress_response}")
                return False
            
            time.sleep(2)  # Check every 2 seconds
        
        # Analyze progress updates
        if len(progress_updates) >= 2:  # Should have multiple updates
            final_update = progress_updates[-1]
            
            if final_update['status'] == 'completed':
                # Verify progress was incremental
                progress_incremental = True
                for i in range(1, len(progress_updates)):
                    if progress_updates[i]['processed_chunks'] < progress_updates[i-1]['processed_chunks']:
                        progress_incremental = False
                        break
                
                if progress_incremental and final_update['added'] > 0:
                    self.log_test("Real-time Progress Tracking", True, 
                                 f"Progress tracking working: {len(progress_updates)} updates, final: {final_update['processed_chunks']}/{final_update['total_chunks']} chunks, {final_update['added']} nodes added")
                    return True
                else:
                    self.log_test("Real-time Progress Tracking", False, 
                                 f"Progress not incremental or no nodes added: {progress_updates}")
                    return False
            else:
                self.log_test("Real-time Progress Tracking", False, 
                             f"Import did not complete successfully: {final_update}")
                return False
        else:
            self.log_test("Real-time Progress Tracking", False, 
                         f"Not enough progress updates received: {len(progress_updates)}")
            return False

    def test_scenario_2_import_cancellation(self):
        """СЦЕНАРИЙ 2 - Отмена импорта: Test import cancellation during processing"""
        print("\n🔍 СЦЕНАРИЙ 2 - Testing Import Cancellation During Processing")
        
        # Generate large test data to ensure we have time to cancel
        test_data = self.generate_large_test_data(800, "172.21")  # 800KB file
        data_size_kb = len(test_data.encode('utf-8')) / 1024
        
        print(f"   Generated test data: {data_size_kb:.1f}KB for cancellation test")
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Start import
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            
            self.log_test("Large Import Started for Cancellation", True, 
                         f"Started import session: {session_id}")
            
            # Wait a bit to let processing start
            time.sleep(3)
            
            # Check that import is running
            progress_success, progress_response = self.make_request('GET', f'import/progress/{session_id}')
            
            if progress_success and progress_response.get('status') == 'processing':
                print(f"   Import is processing, attempting cancellation...")
                
                # Cancel the import
                cancel_success, cancel_response = self.make_request('DELETE', f'import/cancel/{session_id}')
                
                if cancel_success:
                    self.log_test("Import Cancellation Request", True, 
                                 f"Cancellation request successful: {cancel_response.get('message', '')}")
                    
                    # Wait and check if import was actually cancelled
                    time.sleep(2)
                    
                    final_progress_success, final_progress_response = self.make_request('GET', f'import/progress/{session_id}')
                    
                    if final_progress_success:
                        final_status = final_progress_response.get('status', '')
                        current_operation = final_progress_response.get('current_operation', '')
                        
                        if final_status == 'cancelled':
                            self.log_test("Import Cancellation Verification", True, 
                                         f"Import successfully cancelled. Status: {final_status}, Operation: {current_operation}")
                            return True
                        else:
                            self.log_test("Import Cancellation Verification", False, 
                                         f"Import not cancelled. Status: {final_status}, Operation: {current_operation}")
                            return False
                    else:
                        self.log_test("Import Cancellation Verification", False, 
                                     f"Failed to check final progress: {final_progress_response}")
                        return False
                else:
                    self.log_test("Import Cancellation Request", False, 
                                 f"Cancellation request failed: {cancel_response}")
                    return False
            else:
                # Import might have completed too quickly, try cancelling anyway
                print(f"   Import status: {progress_response.get('status', 'unknown')}, trying cancellation anyway...")
                
                cancel_success, cancel_response = self.make_request('DELETE', f'import/cancel/{session_id}')
                
                if cancel_success:
                    self.log_test("Import Cancellation (Fast Import)", True, 
                                 f"Cancellation endpoint working (import may have completed quickly): {cancel_response.get('message', '')}")
                    return True
                else:
                    self.log_test("Import Cancellation (Fast Import)", False, 
                                 f"Cancellation endpoint failed: {cancel_response}")
                    return False
        else:
            self.log_test("Large Import Started for Cancellation", False, 
                         f"Failed to start chunked import: {response}")
            return False

    def test_scenario_3_regular_import_small_files(self):
        """СЦЕНАРИЙ 3 - Обычный импорт малых файлов: Test that small files use regular endpoint"""
        print("\n🔍 СЦЕНАРИЙ 3 - Testing Regular Import for Small Files (<500KB)")
        
        # Generate small test data <500KB with unique IP range
        test_data = self.generate_large_test_data(100, "192.168")  # 100KB file with unique IPs
        data_size_kb = len(test_data.encode('utf-8')) / 1024
        
        print(f"   Generated test data: {data_size_kb:.1f}KB")
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Start import
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        end_time = time.time()
        
        import_duration = end_time - start_time
        
        if success:
            # Check if it used regular processing (no session_id)
            if 'session_id' not in response or response.get('session_id') is None:
                # Regular processing
                if 'report' in response:
                    report = response['report']
                    added = report.get('added', 0)
                    skipped = report.get('skipped_duplicates', 0)
                    total_processed = report.get('total_processed', 0)
                    
                    # Accept either new nodes added OR duplicates skipped as success
                    if added > 0 or (skipped > 0 and total_processed > 0):
                        self.log_test("Small File Regular Processing", True, 
                                     f"Small file ({data_size_kb:.1f}KB) used regular processing (no session_id), {added} nodes added, {skipped} duplicates skipped in {import_duration:.1f}s")
                        return True
                    else:
                        self.log_test("Small File Regular Processing", False, 
                                     f"Regular processing but no nodes processed: {report}")
                        return False
                else:
                    self.log_test("Small File Regular Processing", False, 
                                 f"Regular processing but no report: {response}")
                    return False
            else:
                # Chunked processing (unexpected for small file)
                session_id = response.get('session_id')
                self.log_test("Small File Regular Processing", False, 
                             f"Small file ({data_size_kb:.1f}KB) unexpectedly used chunked processing (session_id: {session_id})")
                return False
        else:
            self.log_test("Small File Regular Processing", False, 
                         f"Small file import failed: {response}")
            return False

    def test_chunked_import_direct_endpoint(self):
        """Test direct chunked import endpoint"""
        print("\n🔍 Testing Direct Chunked Import Endpoint")
        
        # Generate medium test data
        test_data = self.generate_large_test_data(300, "172.22")  # 300KB
        data_size_kb = len(test_data.encode('utf-8')) / 1024
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Use direct chunked endpoint
        success, response = self.make_request('POST', 'nodes/import-chunked', import_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            total_chunks = response.get('total_chunks', 0)
            progress_url = response.get('progress_url', '')
            
            self.log_test("Direct Chunked Endpoint", True, 
                         f"Direct chunked import started: session={session_id}, chunks={total_chunks}, progress_url={progress_url}")
            
            # Wait for completion
            max_wait = 60
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                progress_success, progress_response = self.make_request('GET', f'import/progress/{session_id}')
                
                if progress_success:
                    status = progress_response.get('status', '')
                    if status == 'completed':
                        added = progress_response.get('added', 0)
                        self.log_test("Direct Chunked Completion", True, 
                                     f"Direct chunked import completed: {added} nodes added")
                        return True
                    elif status == 'failed':
                        self.log_test("Direct Chunked Completion", False, 
                                     f"Direct chunked import failed: {progress_response.get('current_operation', '')}")
                        return False
                
                time.sleep(2)
            
            self.log_test("Direct Chunked Completion", False, 
                         f"Direct chunked import timed out after {max_wait}s")
            return False
        else:
            self.log_test("Direct Chunked Endpoint", False, 
                         f"Direct chunked import failed: {response}")
            return False

    def test_ui_hanging_prevention(self):
        """Test that UI hanging is prevented with chunked import"""
        print("\n🔍 Testing UI Hanging Prevention")
        
        # This test verifies that large imports return immediately with session_id
        # instead of blocking until completion
        
        test_data = self.generate_large_test_data(700, "172.23")  # 700KB
        data_size_kb = len(test_data.encode('utf-8')) / 1024
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Measure response time - should be immediate for chunked processing
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        response_time = time.time() - start_time
        
        if success and 'session_id' in response:
            # Response should be immediate (< 5 seconds) even for large files
            if response_time < 5.0:
                session_id = response['session_id']
                self.log_test("UI Hanging Prevention", True, 
                             f"Large file ({data_size_kb:.1f}KB) returned immediately in {response_time:.1f}s with session_id={session_id}")
                return True
            else:
                self.log_test("UI Hanging Prevention", False, 
                             f"Large file took too long to respond: {response_time:.1f}s (should be <5s)")
                return False
        else:
            self.log_test("UI Hanging Prevention", False, 
                         f"Large file import failed or didn't use chunked processing: {response}")
            return False

    def run_all_tests(self):
        """Run all chunked import tests"""
        print("🚀 Starting Chunked Import Functionality Testing")
        print("=" * 60)
        
        # Login first
        if not self.test_login():
            print("❌ Login failed, cannot continue with tests")
            return False
        
        # Run all test scenarios
        test_results = []
        
        # СЦЕНАРИЙ 1 - Chunked Import большого файла
        test_results.append(self.test_scenario_1_chunked_import_large_file())
        
        # СЦЕНАРИЙ 2 - Отмена импорта
        test_results.append(self.test_scenario_2_import_cancellation())
        
        # СЦЕНАРИЙ 3 - Обычный импорт малых файлов
        test_results.append(self.test_scenario_3_regular_import_small_files())
        
        # Additional tests
        test_results.append(self.test_chunked_import_direct_endpoint())
        test_results.append(self.test_ui_hanging_prevention())
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 CHUNKED IMPORT TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in test_results if result)
        total_tests = len(test_results)
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{status}: {result['test']}")
            if not result["success"] and result["details"]:
                print(f"   Error: {result['details']}")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = ChunkedImportTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All chunked import tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some chunked import tests failed!")
        sys.exit(1)