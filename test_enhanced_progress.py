#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class EnhancedProgressTester:
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

    def test_enhanced_progress_chunked_import_large_file(self):
        """SCENARIO 1: Test chunked import with visual progress for large files (>500KB, 1000+ nodes)"""
        print("\n🔍 SCENARIO 1: Testing chunked import with visual progress...")
        
        # Generate large file data (>500KB, approximately 1000+ nodes)
        test_nodes = []
        for i in range(15000):  # Generate 15000 nodes to ensure >500KB
            ip_third = (i // 256) + 100
            ip_fourth = i % 256
            # Make each line longer to reach 500KB threshold
            test_nodes.append(f"10.{ip_third}.{ip_fourth}.1:progressuser{i}_with_longer_name:progresspass{i}_with_longer_password")
        
        test_data = "\n".join(test_nodes)
        data_size = len(test_data.encode('utf-8'))
        
        print(f"📊 Generated test data: {len(test_nodes)} nodes, {data_size/1024:.1f}KB")
        
        if data_size <= 500 * 1024:
            self.log_test("Enhanced Progress - Large File Size", False, 
                         f"Test data too small: {data_size/1024:.1f}KB (need >500KB)")
            return False
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Start chunked import
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            total_chunks = response.get('total_chunks', 0)
            
            print(f"✅ Chunked import started: session_id={session_id}, total_chunks={total_chunks}")
            
            # Monitor progress with visual feedback
            progress_checks = 0
            last_progress = 0
            processing_speeds = []
            
            while progress_checks < 30:  # Max 30 checks (30 seconds)
                time.sleep(1)  # Check every second
                progress_checks += 1
                
                # Get progress
                progress_success, progress_response = self.make_request('GET', f'import/progress/{session_id}')
                
                if progress_success:
                    status = progress_response.get('status', 'unknown')
                    processed_chunks = progress_response.get('processed_chunks', 0)
                    total_chunks = progress_response.get('total_chunks', 1)
                    added = progress_response.get('added', 0)
                    skipped = progress_response.get('skipped', 0)
                    errors = progress_response.get('errors', 0)
                    current_operation = progress_response.get('current_operation', '')
                    
                    # Calculate progress percentage
                    progress_percent = int((processed_chunks / total_chunks) * 100) if total_chunks > 0 else 0
                    
                    # Calculate processing speed (nodes/sec)
                    elapsed_time = time.time() - start_time
                    nodes_per_sec = added / elapsed_time if elapsed_time > 0 else 0
                    processing_speeds.append(nodes_per_sec)
                    
                    # Visual progress display
                    if progress_percent > last_progress:
                        print(f"📈 Progress: {progress_percent}% ({processed_chunks}/{total_chunks} chunks) | "
                              f"Added: {added}, Skipped: {skipped}, Errors: {errors} | "
                              f"Speed: {nodes_per_sec:.1f} nodes/sec | {current_operation}")
                        last_progress = progress_percent
                    
                    if status == 'completed':
                        print(f"✅ Import completed: {added} added, {skipped} skipped, {errors} errors")
                        break
                    elif status == 'failed':
                        print(f"❌ Import failed: {current_operation}")
                        break
                else:
                    print(f"⚠️ Progress check failed: {progress_response}")
            
            # Verify final results
            if progress_checks < 30:  # Completed within time limit
                # Check that progress was properly tracked
                if len(processing_speeds) > 0 and max(processing_speeds) > 0:
                    avg_speed = sum(processing_speeds) / len(processing_speeds)
                    max_speed = max(processing_speeds)
                    
                    self.log_test("Enhanced Progress - Chunked Import Large File", True, 
                                 f"Large file chunked import with progress tracking successful: "
                                 f"{added} nodes added, avg speed: {avg_speed:.1f} nodes/sec, max speed: {max_speed:.1f} nodes/sec")
                    return True
                else:
                    self.log_test("Enhanced Progress - Chunked Import Large File", False, 
                                 f"Progress tracking failed - no processing speed detected")
                    return False
            else:
                self.log_test("Enhanced Progress - Chunked Import Large File", False, 
                             f"Import timed out after 30 seconds")
                return False
        else:
            self.log_test("Enhanced Progress - Chunked Import Large File", False, 
                         f"Failed to start chunked import: {response}")
            return False
    
    def test_enhanced_progress_regular_import_small_file(self):
        """SCENARIO 2: Test regular import with simple indicator for small files (<500KB, ~100 nodes)"""
        print("\n🔍 SCENARIO 2: Testing regular import with simple indicator...")
        
        # Generate small file data (<500KB, approximately 100 nodes)
        test_nodes = []
        for i in range(100):
            test_nodes.append(f"172.16.{i//256}.{i%256}:simpleuser{i}:simplepass{i}")
        
        test_data = "\n".join(test_nodes)
        data_size = len(test_data.encode('utf-8'))
        
        print(f"📊 Generated test data: {len(test_nodes)} nodes, {data_size/1024:.1f}KB")
        
        if data_size >= 500 * 1024:
            self.log_test("Enhanced Progress - Small File Size", False, 
                         f"Test data too large: {data_size/1024:.1f}KB (need <500KB)")
            return False
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Start regular import
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        end_time = time.time()
        
        import_duration = end_time - start_time
        
        if success and 'report' in response:
            report = response['report']
            added = report.get('added', 0)
            skipped = report.get('skipped_duplicates', 0)
            errors = report.get('format_errors', 0)
            
            # Verify no session_id (regular import, not chunked)
            session_id = response.get('session_id')
            
            if session_id is None:
                # Calculate processing speed
                nodes_per_sec = added / import_duration if import_duration > 0 else 0
                
                self.log_test("Enhanced Progress - Regular Import Small File", True, 
                             f"Small file regular import successful: {added} nodes added in {import_duration:.1f}s "
                             f"({nodes_per_sec:.1f} nodes/sec), no session_id (simple indicator mode)")
                return True
            else:
                self.log_test("Enhanced Progress - Regular Import Small File", False, 
                             f"Small file incorrectly used chunked processing (session_id: {session_id})")
                return False
        else:
            self.log_test("Enhanced Progress - Regular Import Small File", False, 
                         f"Failed to import small file: {response}")
            return False
    
    def test_enhanced_progress_cancel_functionality(self):
        """Test cancel button functionality during chunked import"""
        print("\n🔍 Testing import cancellation functionality...")
        
        # Generate medium-large file for cancellation test (ensure >500KB for chunked processing)
        test_nodes = []
        for i in range(12000):  # Generate enough nodes for cancellation test
            test_nodes.append(f"192.168.{i//256}.{i%256}:canceluser{i}_longer_name:cancelpass{i}_longer_password")
        
        test_data = "\n".join(test_nodes)
        data_size = len(test_data.encode('utf-8'))
        print(f"📊 Generated cancellation test data: {len(test_nodes)} nodes, {data_size/1024:.1f}KB")
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Start chunked import
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            print(f"✅ Import started for cancellation test: session_id={session_id}")
            
            # Wait a moment for processing to start
            time.sleep(2)
            
            # Check initial progress
            progress_success, progress_response = self.make_request('GET', f'import/progress/{session_id}')
            if progress_success:
                initial_status = progress_response.get('status', 'unknown')
                initial_processed = progress_response.get('processed_chunks', 0)
                print(f"📊 Initial progress: status={initial_status}, processed={initial_processed}")
            
            # Cancel the import
            cancel_success, cancel_response = self.make_request('DELETE', f'import/cancel/{session_id}')
            
            if cancel_success:
                print(f"✅ Cancel request successful: {cancel_response.get('message', 'No message')}")
                
                # Wait a moment for cancellation to take effect
                time.sleep(2)
                
                # Check final progress
                final_progress_success, final_progress_response = self.make_request('GET', f'import/progress/{session_id}')
                
                if final_progress_success:
                    final_status = final_progress_response.get('status', 'unknown')
                    final_operation = final_progress_response.get('current_operation', '')
                    
                    if final_status == 'cancelled':
                        self.log_test("Enhanced Progress - Cancel Functionality", True, 
                                     f"Import cancellation successful: status={final_status}, operation='{final_operation}'")
                        return True
                    else:
                        self.log_test("Enhanced Progress - Cancel Functionality", False, 
                                     f"Import not properly cancelled: status={final_status}")
                        return False
                else:
                    self.log_test("Enhanced Progress - Cancel Functionality", False, 
                                 f"Failed to check final progress after cancellation")
                    return False
            else:
                self.log_test("Enhanced Progress - Cancel Functionality", False, 
                             f"Failed to cancel import: {cancel_response}")
                return False
        else:
            self.log_test("Enhanced Progress - Cancel Functionality", False, 
                         f"Failed to start import for cancellation test: {response}")
            return False

    def run_enhanced_progress_tests(self):
        """Run enhanced progress interface tests"""
        print("🚀 Starting Enhanced Progress Interface Testing")
        print("🎯" * 60)
        print("🇷🇺 ТЕСТИРОВАНИЕ УЛУЧШЕННОГО ПРОГРЕСС-ИНТЕРФЕЙСА")
        print("ОБНОВЛЕНИЯ:")
        print("1. Большой процентный индикатор: 2xl размер шрифта для % в центре карточки")
        print("2. Улучшенный прогресс-бар: Градиент, анимация, процент внутри бара")
        print("3. Скорость обработки: Показывает узлов/сек для понимания скорости")
        print("4. Детальная статистика: 4 колонки с большими цифрами (Добавлено/Пропущено/Ошибок/Всего)")
        print("5. Активный индикатор: Анимированные точки показывают что процесс идет")
        print("6. Кнопка отмены: Перемещена в заголовок для легкого доступа")
        print("🎯" * 60)
        
        # Test authentication first
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Run enhanced progress tests
        self.test_enhanced_progress_chunked_import_large_file()
        self.test_enhanced_progress_regular_import_small_file()
        self.test_enhanced_progress_cancel_functionality()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"🏁 Enhanced Progress Testing Complete: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📊 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL ENHANCED PROGRESS TESTS PASSED!")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = EnhancedProgressTester()
    success = tester.run_enhanced_progress_tests()
    sys.exit(0 if success else 1)