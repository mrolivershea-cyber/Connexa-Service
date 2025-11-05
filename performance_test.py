#!/usr/bin/env python3

import requests
import sys
import json
import time
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List

class PerformanceTester:
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

    def test_logout(self):
        """Test logout functionality"""
        success, response = self.make_request('POST', 'auth/logout')
        
        if success:
            self.log_test("Logout", True, "Logged out successfully")
            return True
        else:
            self.log_test("Logout", False, f"Failed to logout: {response}")
            return False

    def test_performance_api_nodes_filters(self):
        """Test GET /api/nodes with various filters - should be < 200ms"""
        print("\n🚀 PERFORMANCE TEST: GET /api/nodes with filters")
        print("=" * 60)
        
        filter_combinations = [
            {"ip": "192.168"},
            {"provider": "CloudVPN"},
            {"country": "United States"},
            {"state": "California"},
            {"city": "Los Angeles"},
            {"status": "not_tested"},
            {"protocol": "pptp"},
            {"ip": "10.0", "status": "not_tested"},
            {"provider": "VPN", "country": "United States"},
            {"state": "California", "city": "Los Angeles"},
            {"country": "United States", "status": "not_tested", "protocol": "pptp"}
        ]
        
        performance_results = []
        
        for i, filters in enumerate(filter_combinations, 1):
            start_time = time.time()
            success, response = self.make_request('GET', 'nodes', filters)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if success and 'nodes' in response:
                total_nodes = response.get('total', 0)
                returned_nodes = len(response['nodes'])
                
                performance_results.append({
                    'test': f"Filter Test {i}",
                    'filters': filters,
                    'response_time_ms': response_time_ms,
                    'total_nodes': total_nodes,
                    'returned_nodes': returned_nodes,
                    'passed': response_time_ms < 200
                })
                
                status = "✅ PASS" if response_time_ms < 200 else "❌ FAIL"
                print(f"   {status} Filter {i}: {response_time_ms:.1f}ms (< 200ms target) - {total_nodes} total, {returned_nodes} returned")
                print(f"      Filters: {filters}")
            else:
                performance_results.append({
                    'test': f"Filter Test {i}",
                    'filters': filters,
                    'response_time_ms': response_time_ms,
                    'total_nodes': 0,
                    'returned_nodes': 0,
                    'passed': False
                })
                print(f"   ❌ FAIL Filter {i}: Request failed - {response}")
        
        # Calculate overall performance
        passed_tests = sum(1 for r in performance_results if r['passed'])
        avg_response_time = sum(r['response_time_ms'] for r in performance_results) / len(performance_results)
        max_response_time = max(r['response_time_ms'] for r in performance_results)
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Tests Passed: {passed_tests}/{len(performance_results)}")
        print(f"   Average Response Time: {avg_response_time:.1f}ms")
        print(f"   Max Response Time: {max_response_time:.1f}ms")
        print(f"   Target: < 200ms")
        
        overall_success = passed_tests == len(performance_results) and avg_response_time < 200
        
        self.log_test("Performance - API Nodes Filters", overall_success,
                     f"{passed_tests}/{len(performance_results)} filters < 200ms, avg: {avg_response_time:.1f}ms")
        
        return overall_success

    def test_performance_nodes_all_ids(self):
        """Test GET /api/nodes/all-ids endpoint performance - should be < 500ms"""
        print("\n🚀 PERFORMANCE TEST: GET /api/nodes/all-ids")
        print("=" * 60)
        
        filter_combinations = [
            {},  # No filters - get all IDs
            {"status": "not_tested"},
            {"protocol": "pptp"},
            {"country": "United States"},
            {"state": "California"},
            {"provider": "VPN"},
            {"status": "not_tested", "protocol": "pptp"},
            {"country": "United States", "state": "California"}
        ]
        
        performance_results = []
        
        for i, filters in enumerate(filter_combinations, 1):
            start_time = time.time()
            success, response = self.make_request('GET', 'nodes/all-ids', filters)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            if success and 'node_ids' in response:
                total_ids = response.get('total_count', 0)
                
                performance_results.append({
                    'test': f"All-IDs Test {i}",
                    'filters': filters,
                    'response_time_ms': response_time_ms,
                    'total_ids': total_ids,
                    'passed': response_time_ms < 500
                })
                
                status = "✅ PASS" if response_time_ms < 500 else "❌ FAIL"
                print(f"   {status} All-IDs {i}: {response_time_ms:.1f}ms (< 500ms target) - {total_ids} IDs")
                print(f"      Filters: {filters}")
            else:
                performance_results.append({
                    'test': f"All-IDs Test {i}",
                    'filters': filters,
                    'response_time_ms': response_time_ms,
                    'total_ids': 0,
                    'passed': False
                })
                print(f"   ❌ FAIL All-IDs {i}: Request failed - {response}")
        
        # Calculate overall performance
        passed_tests = sum(1 for r in performance_results if r['passed'])
        avg_response_time = sum(r['response_time_ms'] for r in performance_results) / len(performance_results)
        max_response_time = max(r['response_time_ms'] for r in performance_results)
        
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Tests Passed: {passed_tests}/{len(performance_results)}")
        print(f"   Average Response Time: {avg_response_time:.1f}ms")
        print(f"   Max Response Time: {max_response_time:.1f}ms")
        print(f"   Target: < 500ms")
        
        overall_success = passed_tests == len(performance_results) and avg_response_time < 500
        
        self.log_test("Performance - Nodes All-IDs", overall_success,
                     f"{passed_tests}/{len(performance_results)} requests < 500ms, avg: {avg_response_time:.1f}ms")
        
        return overall_success

    def test_performance_stats_api(self):
        """Test GET /api/stats endpoint performance - should be < 1000ms"""
        print("\n🚀 PERFORMANCE TEST: GET /api/stats")
        print("=" * 60)
        
        # Test stats endpoint multiple times to get consistent results
        response_times = []
        
        for i in range(5):
            start_time = time.time()
            success, response = self.make_request('GET', 'stats')
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            response_times.append(response_time_ms)
            
            if success and 'total' in response:
                status = "✅ PASS" if response_time_ms < 1000 else "❌ FAIL"
                print(f"   {status} Stats Test {i+1}: {response_time_ms:.1f}ms (< 1000ms target)")
                print(f"      Total nodes: {response.get('total', 0)}")
                print(f"      Status breakdown: not_tested={response.get('not_tested', 0)}, online={response.get('online', 0)}")
            else:
                print(f"   ❌ FAIL Stats Test {i+1}: Request failed - {response}")
                response_times[-1] = 9999  # Mark as failed
        
        # Calculate performance metrics
        valid_times = [t for t in response_times if t < 9999]
        if valid_times:
            avg_response_time = sum(valid_times) / len(valid_times)
            max_response_time = max(valid_times)
            min_response_time = min(valid_times)
            passed_tests = sum(1 for t in valid_times if t < 1000)
            
            print(f"\n📊 PERFORMANCE SUMMARY:")
            print(f"   Tests Passed: {passed_tests}/{len(valid_times)}")
            print(f"   Average Response Time: {avg_response_time:.1f}ms")
            print(f"   Min Response Time: {min_response_time:.1f}ms")
            print(f"   Max Response Time: {max_response_time:.1f}ms")
            print(f"   Target: < 1000ms")
            
            overall_success = passed_tests == len(valid_times) and avg_response_time < 1000
            
            self.log_test("Performance - Stats API", overall_success,
                         f"{passed_tests}/{len(valid_times)} requests < 1000ms, avg: {avg_response_time:.1f}ms")
            
            return overall_success
        else:
            self.log_test("Performance - Stats API", False, "All stats requests failed")
            return False

    def test_performance_concurrent_requests(self):
        """Test concurrent API requests to verify no performance degradation"""
        print("\n🚀 PERFORMANCE TEST: Concurrent API Requests")
        print("=" * 60)
        
        # Test concurrent requests to different endpoints
        endpoints_to_test = [
            ('GET', 'nodes', {'limit': 50}),
            ('GET', 'stats', {}),
            ('GET', 'nodes/all-ids', {'status': 'not_tested'}),
            ('GET', 'nodes', {'protocol': 'pptp', 'limit': 50}),
            ('GET', 'autocomplete/countries', {})
        ]
        
        results_queue = queue.Queue()
        
        def make_concurrent_request(endpoint_data, thread_id):
            method, endpoint, params = endpoint_data
            start_time = time.time()
            success, response = self.make_request(method, endpoint, params)
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            results_queue.put({
                'thread_id': thread_id,
                'endpoint': endpoint,
                'method': method,
                'success': success,
                'response_time_ms': response_time_ms,
                'response': response
            })
        
        # Start concurrent requests
        threads = []
        start_time = time.time()
        
        for i, endpoint_data in enumerate(endpoints_to_test):
            thread = threading.Thread(target=make_concurrent_request, args=(endpoint_data, i+1))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = (time.time() - start_time) * 1000
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            avg_response_time = sum(r['response_time_ms'] for r in successful_requests) / len(successful_requests)
            max_response_time = max(r['response_time_ms'] for r in successful_requests)
            
            print(f"📊 CONCURRENT REQUEST RESULTS:")
            print(f"   Total Requests: {len(results)}")
            print(f"   Successful: {len(successful_requests)}")
            print(f"   Failed: {len(failed_requests)}")
            print(f"   Total Time: {total_time:.1f}ms")
            print(f"   Average Response Time: {avg_response_time:.1f}ms")
            print(f"   Max Response Time: {max_response_time:.1f}ms")
            
            for result in successful_requests:
                status = "✅" if result['response_time_ms'] < 2000 else "⚠️"
                print(f"   {status} Thread {result['thread_id']} ({result['endpoint']}): {result['response_time_ms']:.1f}ms")
            
            for result in failed_requests:
                print(f"   ❌ Thread {result['thread_id']} ({result['endpoint']}): FAILED")
            
            # Success criteria: all requests successful, no request > 2000ms, avg < 1000ms
            overall_success = (len(failed_requests) == 0 and 
                             max_response_time < 2000 and 
                             avg_response_time < 1000)
            
            self.log_test("Performance - Concurrent Requests", overall_success,
                         f"{len(successful_requests)}/{len(results)} successful, avg: {avg_response_time:.1f}ms, max: {max_response_time:.1f}ms")
            
            return overall_success
        else:
            self.log_test("Performance - Concurrent Requests", False, "All concurrent requests failed")
            return False

    def test_performance_database_indexes(self):
        """Test database index effectiveness by comparing filtered vs unfiltered queries"""
        print("\n🚀 PERFORMANCE TEST: Database Index Verification")
        print("=" * 60)
        
        # Test queries that should benefit from indexes
        indexed_queries = [
            {"filter": {"provider": "CloudVPN"}, "description": "Provider index"},
            {"filter": {"country": "United States"}, "description": "Country index"},
            {"filter": {"state": "California"}, "description": "State index"},
            {"filter": {"city": "Los Angeles"}, "description": "City index"},
            {"filter": {"status": "not_tested"}, "description": "Status index"},
            {"filter": {"protocol": "pptp"}, "description": "Protocol index"},
            {"filter": {"zipcode": "90210"}, "description": "Zipcode index"},
            {"filter": {"login": "admin"}, "description": "Login index"}
        ]
        
        performance_results = []
        
        # First, get baseline performance with no filters
        start_time = time.time()
        success, baseline_response = self.make_request('GET', 'nodes', {'limit': 200})
        baseline_time = (time.time() - start_time) * 1000
        
        if success:
            baseline_total = baseline_response.get('total', 0)
            print(f"📊 Baseline (no filters): {baseline_time:.1f}ms - {baseline_total} total nodes")
        else:
            print(f"❌ Baseline query failed: {baseline_response}")
            self.log_test("Performance - Database Indexes", False, "Baseline query failed")
            return False
        
        # Test each indexed query
        for query_data in indexed_queries:
            filters = query_data["filter"]
            description = query_data["description"]
            
            start_time = time.time()
            success, response = self.make_request('GET', 'nodes', filters)
            response_time = (time.time() - start_time) * 1000
            
            if success and 'nodes' in response:
                total_nodes = response.get('total', 0)
                returned_nodes = len(response['nodes'])
                
                # Index is effective if filtered query is not significantly slower than baseline
                # Allow up to 3x baseline time for complex filters
                index_effective = response_time <= (baseline_time * 3)
                
                performance_results.append({
                    'description': description,
                    'filters': filters,
                    'response_time_ms': response_time,
                    'total_nodes': total_nodes,
                    'returned_nodes': returned_nodes,
                    'index_effective': index_effective
                })
                
                status = "✅ EFFECTIVE" if index_effective else "⚠️ SLOW"
                print(f"   {status} {description}: {response_time:.1f}ms - {total_nodes} total, {returned_nodes} returned")
                print(f"      Filter: {filters}")
            else:
                performance_results.append({
                    'description': description,
                    'filters': filters,
                    'response_time_ms': 9999,
                    'total_nodes': 0,
                    'returned_nodes': 0,
                    'index_effective': False
                })
                print(f"   ❌ FAILED {description}: Request failed - {response}")
        
        # Calculate overall index effectiveness
        effective_indexes = sum(1 for r in performance_results if r['index_effective'])
        avg_response_time = sum(r['response_time_ms'] for r in performance_results if r['response_time_ms'] < 9999)
        if performance_results:
            avg_response_time = avg_response_time / len([r for r in performance_results if r['response_time_ms'] < 9999])
        
        print(f"\n📊 INDEX EFFECTIVENESS SUMMARY:")
        print(f"   Effective Indexes: {effective_indexes}/{len(performance_results)}")
        print(f"   Average Filtered Query Time: {avg_response_time:.1f}ms")
        print(f"   Baseline Query Time: {baseline_time:.1f}ms")
        print(f"   Performance Ratio: {avg_response_time/baseline_time:.1f}x baseline")
        
        # Success criteria: at least 75% of indexes are effective
        overall_success = (effective_indexes / len(performance_results)) >= 0.75
        
        self.log_test("Performance - Database Indexes", overall_success,
                     f"{effective_indexes}/{len(performance_results)} indexes effective, avg: {avg_response_time:.1f}ms vs baseline: {baseline_time:.1f}ms")
        
        return overall_success

    def run_performance_tests(self):
        """Run all performance optimization tests"""
        print(f"🚀 Starting Admin Panel Performance Optimization Tests - {datetime.now()}")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 80)
        
        # Authentication required for all tests
        if not self.test_login():
            print("❌ Login failed - stopping performance tests")
            return False
        
        # Run all performance tests
        performance_results = []
        
        performance_results.append(self.test_performance_api_nodes_filters())
        performance_results.append(self.test_performance_nodes_all_ids())
        performance_results.append(self.test_performance_stats_api())
        performance_results.append(self.test_performance_concurrent_requests())
        performance_results.append(self.test_performance_database_indexes())
        
        # Performance test summary
        passed_tests = sum(performance_results)
        total_tests = len(performance_results)
        
        print("\n" + "=" * 80)
        print(f"🏁 PERFORMANCE TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 All performance tests passed! Admin panel optimizations are working correctly.")
        else:
            print(f"⚠️  {total_tests - passed_tests} performance tests failed - optimizations may need review")
        
        # Logout
        self.test_logout()
        
        return passed_tests == total_tests

    def test_import_performance_small_file_regular(self):
        """ТЕСТ 1: Маленький файл (10 строк) - Regular Import"""
        print(f"\n🔥 ДИАГНОСТИКА ПРОИЗВОДИТЕЛЬНОСТИ ИМПОРТА - ТЕСТ 1: Маленький файл (10 строк)")
        
        # Generate 10 lines in Format 7 (IP:Login:Pass)
        test_data_lines = []
        for i in range(10):
            test_data_lines.append(f"5.78.0.{i+1}:admin:pass{i+1}")
        
        test_data = "\n".join(test_data_lines)
        data_size = len(test_data.encode('utf-8'))
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        print(f"📊 Данные: {len(test_data_lines)} строк, {data_size} байт")
        print(f"📝 Формат: IP:Login:Pass (Format 7)")
        
        # Measure execution time
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        if success and 'report' in response:
            report = response['report']
            added_count = report.get('added', 0)
            skipped_count = report.get('skipped_duplicates', 0)
            errors_count = report.get('format_errors', 0) + report.get('processing_errors', 0)
            
            self.log_test("Import Performance - Small File (10 lines)", True, 
                         f"✅ Время выполнения: {execution_time:.3f}s, Добавлено: {added_count}, Пропущено: {skipped_count}, Ошибки: {errors_count}")
            
            print(f"⏱️  Время выполнения: {execution_time:.3f} секунд")
            print(f"📈 Добавлено узлов: {added_count}")
            print(f"⚠️  Дубликатов пропущено: {skipped_count}")
            print(f"❌ Ошибок: {errors_count}")
            
            return {
                'success': True,
                'execution_time': execution_time,
                'added_count': added_count,
                'skipped_count': skipped_count,
                'errors_count': errors_count,
                'data_size': data_size
            }
        else:
            self.log_test("Import Performance - Small File (10 lines)", False, 
                         f"❌ Импорт не удался: {response}")
            print(f"❌ Импорт не удался: {response}")
            return {
                'success': False,
                'execution_time': execution_time,
                'error': response
            }
    
    def test_import_performance_medium_file_regular(self):
        """ТЕСТ 2: Средний файл (1000 строк) - Regular Import"""
        print(f"\n🔥 ДИАГНОСТИКА ПРОИЗВОДИТЕЛЬНОСТИ ИМПОРТА - ТЕСТ 2: Средний файл (1000 строк)")
        
        # Generate 1000 lines in Format 7 (IP:Login:Pass)
        test_data_lines = []
        for i in range(1000):
            ip_c = (i // 256) + 1
            ip_d = i % 256
            test_data_lines.append(f"5.79.{ip_c}.{ip_d}:admin:pass{i+1}")
        
        test_data = "\n".join(test_data_lines)
        data_size = len(test_data.encode('utf-8'))
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        print(f"📊 Данные: {len(test_data_lines)} строк, {data_size} байт ({data_size/1024:.1f} KB)")
        print(f"📝 Формат: IP:Login:Pass (Format 7)")
        
        # Measure execution time
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        if success and 'report' in response:
            report = response['report']
            added_count = report.get('added', 0)
            skipped_count = report.get('skipped_duplicates', 0)
            errors_count = report.get('format_errors', 0) + report.get('processing_errors', 0)
            
            self.log_test("Import Performance - Medium File (1000 lines)", True, 
                         f"✅ Время выполнения: {execution_time:.3f}s, Добавлено: {added_count}, Пропущено: {skipped_count}, Ошибки: {errors_count}")
            
            print(f"⏱️  Время выполнения: {execution_time:.3f} секунд")
            print(f"📈 Добавлено узлов: {added_count}")
            print(f"⚠️  Дубликатов пропущено: {skipped_count}")
            print(f"❌ Ошибок: {errors_count}")
            print(f"🚀 Скорость: {len(test_data_lines)/execution_time:.1f} строк/сек")
            
            return {
                'success': True,
                'execution_time': execution_time,
                'added_count': added_count,
                'skipped_count': skipped_count,
                'errors_count': errors_count,
                'data_size': data_size,
                'processing_speed': len(test_data_lines)/execution_time
            }
        else:
            self.log_test("Import Performance - Medium File (1000 lines)", False, 
                         f"❌ Импорт не удался: {response}")
            print(f"❌ Импорт не удался: {response}")
            return {
                'success': False,
                'execution_time': execution_time,
                'error': response
            }
    
    def test_import_performance_large_file_chunked(self):
        """ТЕСТ 3: Большой файл (5000 строк) - Chunked Import"""
        print(f"\n🔥 ДИАГНОСТИКА ПРОИЗВОДИТЕЛЬНОСТИ ИМПОРТА - ТЕСТ 3: Большой файл (5000 строк)")
        
        # Generate 5000 lines in Format 7 (IP:Login:Pass)
        test_data_lines = []
        for i in range(5000):
            ip_b = (i // 65536) + 80
            ip_c = (i // 256) % 256
            ip_d = i % 256
            test_data_lines.append(f"5.{ip_b}.{ip_c}.{ip_d}:admin:pass{i+1}")
        
        test_data = "\n".join(test_data_lines)
        data_size = len(test_data.encode('utf-8'))
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        print(f"📊 Данные: {len(test_data_lines)} строк, {data_size} байт ({data_size/1024:.1f} KB)")
        print(f"📝 Формат: IP:Login:Pass (Format 7)")
        
        # Measure execution time for chunked import
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import-chunked', import_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            total_chunks = response.get('total_chunks', 0)
            
            print(f"🔄 Chunked import started: session_id={session_id}, total_chunks={total_chunks}")
            
            # Monitor progress until completion
            completed = False
            max_wait_time = 300  # 5 minutes max
            check_interval = 2   # Check every 2 seconds
            checks_made = 0
            max_checks = max_wait_time // check_interval
            
            final_status = None
            final_progress = None
            
            while not completed and checks_made < max_checks:
                time.sleep(check_interval)
                checks_made += 1
                
                progress_success, progress_response = self.make_request('GET', f'import/progress/{session_id}')
                
                if progress_success:
                    status = progress_response.get('status', 'unknown')
                    processed_chunks = progress_response.get('processed_chunks', 0)
                    current_operation = progress_response.get('current_operation', '')
                    
                    print(f"📊 Прогресс: {processed_chunks}/{total_chunks} chunks, статус: {status}, операция: {current_operation}")
                    
                    if status in ['completed', 'failed', 'cancelled']:
                        completed = True
                        final_status = status
                        final_progress = progress_response
                        break
                else:
                    print(f"⚠️  Ошибка получения прогресса: {progress_response}")
            
            end_time = time.time()
            total_execution_time = end_time - start_time
            
            if completed and final_status == 'completed':
                added_count = final_progress.get('added', 0)
                skipped_count = final_progress.get('skipped', 0)
                errors_count = final_progress.get('errors', 0)
                
                self.log_test("Import Performance - Large File Chunked (5000 lines)", True, 
                             f"✅ Общее время: {total_execution_time:.3f}s, Добавлено: {added_count}, Пропущено: {skipped_count}, Ошибки: {errors_count}")
                
                print(f"⏱️  Общее время до завершения: {total_execution_time:.3f} секунд")
                print(f"📈 Добавлено узлов: {added_count}")
                print(f"⚠️  Дубликатов пропущено: {skipped_count}")
                print(f"❌ Ошибок: {errors_count}")
                print(f"🚀 Скорость: {len(test_data_lines)/total_execution_time:.1f} строк/сек")
                print(f"📦 Chunks обработано: {final_progress.get('processed_chunks', 0)}/{total_chunks}")
                
                return {
                    'success': True,
                    'execution_time': total_execution_time,
                    'added_count': added_count,
                    'skipped_count': skipped_count,
                    'errors_count': errors_count,
                    'data_size': data_size,
                    'processing_speed': len(test_data_lines)/total_execution_time,
                    'total_chunks': total_chunks,
                    'session_id': session_id
                }
            else:
                self.log_test("Import Performance - Large File Chunked (5000 lines)", False, 
                             f"❌ Импорт не завершился: статус={final_status}, время={total_execution_time:.3f}s")
                print(f"❌ Импорт не завершился в отведенное время")
                print(f"📊 Финальный статус: {final_status}")
                print(f"⏱️  Время ожидания: {total_execution_time:.3f} секунд")
                
                return {
                    'success': False,
                    'execution_time': total_execution_time,
                    'final_status': final_status,
                    'session_id': session_id
                }
        else:
            end_time = time.time()
            execution_time = end_time - start_time
            
            self.log_test("Import Performance - Large File Chunked (5000 lines)", False, 
                         f"❌ Chunked import не запустился: {response}")
            print(f"❌ Chunked import не запустился: {response}")
            
            return {
                'success': False,
                'execution_time': execution_time,
                'error': response
            }

    def run_import_performance_tests(self):
        """Run import performance tests"""
        print("🔥" * 80)
        print("🇷🇺 ДИАГНОСТИКА ПРОИЗВОДИТЕЛЬНОСТИ ИМПОРТА - REVIEW REQUEST")
        print("🔥" * 80)
        print("ЗАДАЧА: Проверить скорость импорта и найти узкие места")
        print("ТЕСТ 1: Маленький файл (10 строк) - Regular Import")
        print("ТЕСТ 2: Средний файл (1000 строк) - Regular Import")
        print("ТЕСТ 3: Большой файл (5000 строк) - Chunked Import")
        print("ФОРМАТ ДАННЫХ: IP:Login:Pass (Format 7)")
        print("🔥" * 80)
        
        # Login first
        if not self.test_login():
            print("❌ Login failed - stopping tests")
            return False
        
        # Run all three performance tests
        test1_result = self.test_import_performance_small_file_regular()
        test2_result = self.test_import_performance_medium_file_regular()
        test3_result = self.test_import_performance_large_file_chunked()
        
        print(f"\n📊 СВОДКА РЕЗУЛЬТАТОВ ПРОИЗВОДИТЕЛЬНОСТИ")
        print("=" * 80)
        
        # Analyze results
        if test1_result['success']:
            print(f"✅ ТЕСТ 1 (10 строк): {test1_result['execution_time']:.3f}s, {test1_result['added_count']} узлов")
        else:
            print(f"❌ ТЕСТ 1 (10 строк): FAILED")
        
        if test2_result['success']:
            print(f"✅ ТЕСТ 2 (1000 строк): {test2_result['execution_time']:.3f}s, {test2_result['added_count']} узлов, {test2_result['processing_speed']:.1f} строк/сек")
        else:
            print(f"❌ ТЕСТ 2 (1000 строк): FAILED")
        
        if test3_result['success']:
            print(f"✅ ТЕСТ 3 (5000 строк): {test3_result['execution_time']:.3f}s, {test3_result['added_count']} узлов, {test3_result['processing_speed']:.1f} строк/сек")
        else:
            print(f"❌ ТЕСТ 3 (5000 строк): FAILED")
        
        # Identify bottlenecks
        print(f"\n🔍 АНАЛИЗ УЗКИХ МЕСТ:")
        
        if test1_result['success'] and test2_result['success']:
            # Compare per-line processing time
            time_per_line_small = test1_result['execution_time'] / 10
            time_per_line_medium = test2_result['execution_time'] / 1000
            
            print(f"📈 Время на строку (маленький файл): {time_per_line_small*1000:.2f}ms")
            print(f"📈 Время на строку (средний файл): {time_per_line_medium*1000:.2f}ms")
            
            if time_per_line_medium > time_per_line_small * 1.5:
                print(f"⚠️  УЗКОЕ МЕСТО: Производительность падает с увеличением размера файла")
            else:
                print(f"✅ Производительность масштабируется линейно")
        
        if test2_result['success'] and test3_result['success']:
            # Compare regular vs chunked
            regular_speed = test2_result['processing_speed']
            chunked_speed = test3_result['processing_speed']
            
            print(f"🔄 Скорость Regular Import: {regular_speed:.1f} строк/сек")
            print(f"🔄 Скорость Chunked Import: {chunked_speed:.1f} строк/сек")
            
            if chunked_speed < regular_speed * 0.7:
                print(f"⚠️  УЗКОЕ МЕСТО: Chunked import медленнее regular import")
            else:
                print(f"✅ Chunked import показывает хорошую производительность")
        
        # Overall assessment
        all_successful = test1_result['success'] and test2_result['success'] and test3_result['success']
        
        if all_successful:
            print(f"\n🎉 ВСЕ ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ ПРОЙДЕНЫ УСПЕШНО")
            print(f"📊 Результаты тестирования:")
            print(f"   - Маленький файл: {test1_result['execution_time']:.3f}s")
            print(f"   - Средний файл: {test2_result['execution_time']:.3f}s ({test2_result['processing_speed']:.1f} строк/сек)")
            print(f"   - Большой файл: {test3_result['execution_time']:.3f}s ({test3_result['processing_speed']:.1f} строк/сек)")
        else:
            failed_tests = []
            if not test1_result['success']: failed_tests.append("ТЕСТ 1")
            if not test2_result['success']: failed_tests.append("ТЕСТ 2")
            if not test3_result['success']: failed_tests.append("ТЕСТ 3")
            
            print(f"\n❌ НЕУДАЧНЫЕ ТЕСТЫ: {', '.join(failed_tests)}")
        
        print(f"\n📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"✅ Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return all_successful


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "import":
        # Run import performance tests
        tester = PerformanceTester()
        success = tester.run_import_performance_tests()
        sys.exit(0 if success else 1)
    else:
        # Run regular performance tests
        tester = PerformanceTester()
        tester.run_performance_tests()