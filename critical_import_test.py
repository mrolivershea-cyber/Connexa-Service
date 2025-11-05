#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class CriticalImportTester:
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

    def make_request(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200):
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

    def test_critical_regular_import_small_files(self):
        """КРИТИЧЕСКИЙ ТЕСТ 1: Regular Import (малые файлы <200KB) - POST /api/nodes/import"""
        print(f"\n🔥 КРИТИЧЕСКИЙ ТЕСТ 1: Regular Import для малых файлов")
        
        # Generate 50 lines of Format 7 (IP:Login:Pass) as specified
        test_lines = []
        for i in range(50):
            test_lines.append(f"5.78.{i//256}.{i%256+1}:admin:pass{i}")
        
        test_data = "\n".join(test_lines)
        data_size = len(test_data.encode('utf-8'))
        
        print(f"📊 Test data: {len(test_lines)} lines, {data_size} bytes ({data_size/1024:.1f}KB)")
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Test regular import endpoint
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'success' in response and response['success']:
            report = response.get('report', {})
            added = report.get('added', 0)
            skipped = report.get('skipped_duplicates', 0)
            errors = report.get('format_errors', 0)
            
            # Should NOT have session_id for small files
            has_session_id = 'session_id' in response and response['session_id'] is not None
            
            if not has_session_id and added > 0:
                self.log_test("КРИТИЧЕСКИЙ ТЕСТ 1: Regular Import", True, 
                             f"SUCCESS: {added} added, {skipped} skipped, {errors} errors. NO session_id (regular processing)")
                return True
            else:
                self.log_test("КРИТИЧЕСКИЙ ТЕСТ 1: Regular Import", False, 
                             f"Expected regular processing (no session_id), got session_id={response.get('session_id')}")
                return False
        else:
            self.log_test("КРИТИЧЕСКИЙ ТЕСТ 1: Regular Import", False, 
                         f"Import request failed: {response}")
            return False
    
    def test_critical_chunked_import_large_files(self):
        """КРИТИЧЕСКИЙ ТЕСТ 2: Chunked Import (большие файлы >200KB) - POST /api/nodes/import-chunked"""
        print(f"\n🔥 КРИТИЧЕСКИЙ ТЕСТ 2: Chunked Import для больших файлов")
        
        # Generate 1000 lines of Format 7 to ensure >200KB
        test_lines = []
        for i in range(1000):
            # Use different IP ranges to avoid conflicts
            ip_a = 10 + (i // 65536)
            ip_b = (i // 256) % 256
            ip_c = i % 256
            test_lines.append(f"{ip_a}.{ip_b}.{ip_c}.1:admin:pass{i}")
        
        test_data = "\n".join(test_lines)
        data_size = len(test_data.encode('utf-8'))
        
        print(f"📊 Test data: {len(test_lines)} lines, {data_size} bytes ({data_size/1024:.1f}KB)")
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Test chunked import endpoint directly
        success, response = self.make_request('POST', 'nodes/import-chunked', import_data)
        
        if success and 'success' in response and response['success']:
            session_id = response.get('session_id')
            total_chunks = response.get('total_chunks', 0)
            progress_url = response.get('progress_url', '')
            
            if session_id and total_chunks > 0:
                self.log_test("КРИТИЧЕСКИЙ ТЕСТ 2: Chunked Import", True, 
                             f"SUCCESS: session_id={session_id}, total_chunks={total_chunks}, progress_url={progress_url}")
                return session_id  # Return for progress test
            else:
                self.log_test("КРИТИЧЕСКИЙ ТЕСТ 2: Chunked Import", False, 
                             f"Missing session_id or total_chunks. Response: {response}")
                return None
        else:
            self.log_test("КРИТИЧЕСКИЙ ТЕСТ 2: Chunked Import", False, 
                         f"Chunked import request failed: {response}")
            return None
    
    def test_critical_progress_tracking(self):
        """КРИТИЧЕСКИЙ ТЕСТ 3: Progress Tracking - GET /api/import/progress/{session_id}"""
        print(f"\n🔥 КРИТИЧЕСКИЙ ТЕСТ 3: Progress Tracking")
        
        # First start a chunked import to get session_id
        session_id = self.test_critical_chunked_import_large_files()
        
        if not session_id:
            self.log_test("КРИТИЧЕСКИЙ ТЕСТ 3: Progress Tracking", False, 
                         "Could not get session_id from chunked import")
            return False
        
        # Wait a moment for processing to start
        time.sleep(3)
        
        # Test progress tracking endpoint
        success, response = self.make_request('GET', f'import/progress/{session_id}')
        
        if success:
            # Check for required progress fields
            required_fields = ['session_id', 'total_chunks', 'processed_chunks', 'status', 'added', 'skipped', 'errors']
            missing_fields = [field for field in required_fields if field not in response]
            
            if not missing_fields:
                status = response.get('status', 'unknown')
                processed_chunks = response.get('processed_chunks', 0)
                total_chunks = response.get('total_chunks', 0)
                added = response.get('added', 0)
                skipped = response.get('skipped', 0)
                errors = response.get('errors', 0)
                
                self.log_test("КРИТИЧЕСКИЙ ТЕСТ 3: Progress Tracking", True, 
                             f"SUCCESS: status={status}, processed_chunks={processed_chunks}/{total_chunks}, added={added}, skipped={skipped}, errors={errors}")
                return True
            else:
                self.log_test("КРИТИЧЕСКИЙ ТЕСТ 3: Progress Tracking", False, 
                             f"Missing required fields: {missing_fields}")
                return False
        else:
            self.log_test("КРИТИЧЕСКИЙ ТЕСТ 3: Progress Tracking", False, 
                         f"Progress tracking request failed: {response}")
            return False
    
    def test_critical_format_7_comprehensive(self):
        """ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: Comprehensive Format 7 (IP:Login:Pass) validation"""
        print(f"\n🔥 ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: Format 7 Comprehensive Validation")
        
        # Test various Format 7 scenarios
        test_scenarios = [
            ("5.78.0.1:admin:pass1", "Basic Format 7"),
            ("192.168.1.100:user123:complex_pass!@#", "Complex credentials"),
            ("10.0.0.1:test:simple\n10.0.0.2:test2:simple2", "Multiple lines"),
        ]
        
        all_passed = True
        
        for test_data, scenario_name in test_scenarios:
            import_data = {
                "data": test_data,
                "protocol": "pptp"
            }
            
            success, response = self.make_request('POST', 'nodes/import', import_data)
            
            if success and 'report' in response:
                report = response['report']
                added = report.get('added', 0)
                format_errors = report.get('format_errors', 0)
                
                if added > 0 and format_errors == 0:
                    print(f"  ✅ {scenario_name}: {added} nodes added, no format errors")
                else:
                    print(f"  ❌ {scenario_name}: {added} nodes added, {format_errors} format errors")
                    all_passed = False
            else:
                print(f"  ❌ {scenario_name}: Import failed - {response}")
                all_passed = False
        
        self.log_test("ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: Format 7 Comprehensive", all_passed, 
                     "All Format 7 scenarios passed" if all_passed else "Some Format 7 scenarios failed")
        return all_passed
    
    def test_critical_import_endpoints_comparison(self):
        """СРАВНИТЕЛЬНЫЙ ТЕСТ: Compare regular vs chunked import behavior"""
        print(f"\n🔥 СРАВНИТЕЛЬНЫЙ ТЕСТ: Regular vs Chunked Import Behavior")
        
        # Test 1: Small file should use regular import
        small_data = "\n".join([f"172.16.1.{i}:small{i}:pass{i}" for i in range(10)])
        small_size = len(small_data.encode('utf-8'))
        
        import_data_small = {
            "data": small_data,
            "protocol": "pptp"
        }
        
        success_small, response_small = self.make_request('POST', 'nodes/import', import_data_small)
        
        # Test 2: Large file should redirect to chunked
        large_data = "\n".join([f"172.17.{i//256}.{i%256}:large{i}:pass{i}" for i in range(2000)])
        large_size = len(large_data.encode('utf-8'))
        
        import_data_large = {
            "data": large_data,
            "protocol": "pptp"
        }
        
        success_large, response_large = self.make_request('POST', 'nodes/import', import_data_large)
        
        # Analyze results
        small_has_session = 'session_id' in response_small and response_small['session_id'] is not None
        large_has_session = 'session_id' in response_large and response_large['session_id'] is not None
        
        if success_small and success_large:
            if not small_has_session and large_has_session:
                self.log_test("СРАВНИТЕЛЬНЫЙ ТЕСТ: Import Behavior", True, 
                             f"SUCCESS: Small file ({small_size}B) → regular, Large file ({large_size}B) → chunked")
                return True
            else:
                self.log_test("СРАВНИТЕЛЬНЫЙ ТЕСТ: Import Behavior", False, 
                             f"Small session_id={small_has_session}, Large session_id={large_has_session}")
                return False
        else:
            self.log_test("СРАВНИТЕЛЬНЫЙ ТЕСТ: Import Behavior", False, 
                         f"Small success={success_small}, Large success={success_large}")
            return False

    def run_critical_import_tests(self):
        """Run critical import tests only"""
        print("🚀 Starting Critical Import Tests")
        print("=" * 80)
        
        # Test authentication
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        print("\n" + "🔥" * 80)
        print("🇷🇺 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Импорт узлов через API")
        print("🔥" * 80)
        print("КОНТЕКСТ: Пользователь не может импортировать узлы ни через текстовый буфер, ни через файл.")
        print("ТЕСТИРУЕМЫЕ СЦЕНАРИИ:")
        print("1. Regular Import (малые файлы <200KB) - POST /api/nodes/import")
        print("2. Chunked Import (большие файлы >200KB) - POST /api/nodes/import-chunked")
        print("3. Progress Tracking - GET /api/import/progress/{session_id}")
        print("ФОРМАТ ДАННЫХ: Format 7 (IP:Login:Pass)")
        print("🔥" * 80)
        
        # Run critical tests
        self.test_critical_regular_import_small_files()
        self.test_critical_chunked_import_large_files()
        self.test_critical_progress_tracking()
        self.test_critical_format_7_comprehensive()
        self.test_critical_import_endpoints_comparison()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 CRITICAL IMPORT TESTS COMPLETE")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL CRITICAL IMPORT TESTS PASSED!")
        else:
            print(f"❌ {self.tests_run - self.tests_passed} tests failed")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = CriticalImportTester()
    success = tester.run_critical_import_tests()
    sys.exit(0 if success else 1)