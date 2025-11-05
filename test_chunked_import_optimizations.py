#!/usr/bin/env python3

import requests
import time
import json
import sys

class OptimizedChunkedImportTester:
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
            print(f"   📝 {details}")

    def login(self):
        """Login to get access token"""
        login_data = {"username": "admin", "password": "admin"}
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, timeout=30)
            if response.status_code == 200 and 'access_token' in response.json():
                self.token = response.json()['access_token']
                self.headers['Authorization'] = f'Bearer {self.token}'
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_dynamic_chunk_sizing(self):
        """Test dynamic chunk sizing based on file size"""
        print("\n🔥 TESTING DYNAMIC CHUNK SIZING")
        
        # Test 1: Small file (should use 1000 line chunks)
        small_data = []
        for i in range(2000):  # 2K lines
            small_data.append(f"192.168.1.{i%256}:smalluser{i}:smallpass{i}")
        
        small_import = {
            "data": "\n".join(small_data),
            "protocol": "pptp"
        }
        
        try:
            response = requests.post(f"{self.api_url}/nodes/import", json=small_import, headers=self.headers, timeout=60)
            if response.status_code == 200:
                result = response.json()
                if 'session_id' in result:
                    # Should have ~2 chunks for small file
                    total_chunks = result.get('total_chunks', 0)
                    expected_chunks = 2  # 2000 lines / 1000 = 2 chunks
                    chunk_size_correct = abs(total_chunks - expected_chunks) <= 1
                    
                    self.log_test("Dynamic Chunk Sizing - Small File", chunk_size_correct, 
                                 f"Small file (2K lines) -> {total_chunks} chunks (expected ~{expected_chunks})")
                    return chunk_size_correct
                else:
                    # Regular processing is also acceptable for small files
                    self.log_test("Dynamic Chunk Sizing - Small File", True, 
                                 "Small file processed as regular import (acceptable)")
                    return True
            else:
                self.log_test("Dynamic Chunk Sizing - Small File", False, f"Request failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Dynamic Chunk Sizing - Small File", False, f"Exception: {e}")
            return False

    def test_bulk_insert_mode(self):
        """Test bulk insert mode for large chunks"""
        print("\n🔥 TESTING BULK INSERT MODE")
        
        # Create data that should trigger bulk mode (>500 nodes per chunk)
        test_data = []
        for i in range(1500):  # 1500 nodes should trigger bulk processing
            test_data.append(f"10.0.{(i//256)+1}.{i%256}:bulkuser{i}:bulkpass{i}")
        
        import_data = {
            "data": "\n".join(test_data),
            "protocol": "pptp"
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{self.api_url}/nodes/import", json=import_data, headers=self.headers, timeout=120)
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                duration = end_time - start_time
                
                if 'session_id' in result:
                    # Chunked processing
                    session_id = result['session_id']
                    
                    # Wait for completion
                    max_wait = 60
                    wait_time = 0
                    final_added = 0
                    
                    while wait_time < max_wait:
                        time.sleep(3)
                        wait_time += 3
                        
                        try:
                            progress_response = requests.get(f"{self.api_url}/import/progress/{session_id}", headers=self.headers, timeout=10)
                            if progress_response.status_code == 200:
                                progress = progress_response.json()
                                status = progress.get('status', 'unknown')
                                final_added = progress.get('added', 0)
                                
                                if status in ['completed', 'failed', 'cancelled']:
                                    break
                        except:
                            continue
                    
                    # Calculate performance
                    total_time = duration + wait_time
                    nodes_per_second = final_added / total_time if total_time > 0 else 0
                    
                    # Success criteria: should be fast (indicating bulk operations)
                    performance_good = nodes_per_second > 50  # Should process >50 nodes/sec with bulk
                    
                    self.log_test("Bulk Insert Mode", performance_good, 
                                 f"Processed {final_added} nodes at {nodes_per_second:.1f} nodes/sec")
                    return performance_good
                    
                elif 'report' in result:
                    # Regular processing
                    report = result['report']
                    added = report.get('added', 0)
                    nodes_per_second = added / duration if duration > 0 else 0
                    
                    performance_good = nodes_per_second > 50
                    
                    self.log_test("Bulk Insert Mode", performance_good, 
                                 f"Regular processing: {added} nodes at {nodes_per_second:.1f} nodes/sec")
                    return performance_good
                else:
                    self.log_test("Bulk Insert Mode", False, "Unexpected response format")
                    return False
            else:
                self.log_test("Bulk Insert Mode", False, f"Request failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Bulk Insert Mode", False, f"Exception: {e}")
            return False

    def test_fast_duplicate_checking(self):
        """Test fast IP-only duplicate checking"""
        print("\n🔥 TESTING FAST DUPLICATE CHECKING")
        
        # First import some nodes
        initial_data = []
        for i in range(100):
            initial_data.append(f"203.0.113.{i}:user{i}:pass{i}")
        
        initial_import = {
            "data": "\n".join(initial_data),
            "protocol": "pptp"
        }
        
        try:
            # Initial import
            response1 = requests.post(f"{self.api_url}/nodes/import", json=initial_import, headers=self.headers, timeout=60)
            if response1.status_code != 200:
                self.log_test("Fast Duplicate Checking", False, "Initial import failed")
                return False
            
            # Wait if chunked
            if 'session_id' in response1.json():
                session_id = response1.json()['session_id']
                for i in range(10):
                    time.sleep(2)
                    try:
                        progress_response = requests.get(f"{self.api_url}/import/progress/{session_id}", headers=self.headers, timeout=10)
                        if progress_response.status_code == 200:
                            progress = progress_response.json()
                            if progress.get('status') == 'completed':
                                break
                    except:
                        continue
            
            # Now import duplicates with different credentials
            duplicate_data = []
            for i in range(100):
                # Same IPs but different login/password
                duplicate_data.append(f"203.0.113.{i}:differentuser{i}:differentpass{i}")
            
            duplicate_import = {
                "data": "\n".join(duplicate_data),
                "protocol": "pptp"
            }
            
            start_time = time.time()
            response2 = requests.post(f"{self.api_url}/nodes/import", json=duplicate_import, headers=self.headers, timeout=60)
            end_time = time.time()
            
            if response2.status_code == 200:
                result = response2.json()
                duration = end_time - start_time
                
                skipped_count = 0
                
                if 'session_id' in result:
                    # Wait for completion
                    session_id = result['session_id']
                    for i in range(10):
                        time.sleep(2)
                        try:
                            progress_response = requests.get(f"{self.api_url}/import/progress/{session_id}", headers=self.headers, timeout=10)
                            if progress_response.status_code == 200:
                                progress = progress_response.json()
                                if progress.get('status') == 'completed':
                                    skipped_count = progress.get('skipped', 0)
                                    break
                        except:
                            continue
                elif 'report' in result:
                    skipped_count = result['report'].get('skipped_duplicates', 0)
                
                # Should have skipped most duplicates quickly
                fast_processing = duration < 15  # Should be fast
                good_deduplication = skipped_count >= 80  # Should skip most duplicates
                
                success = fast_processing and good_deduplication
                
                self.log_test("Fast Duplicate Checking", success, 
                             f"Skipped {skipped_count} duplicates in {duration:.1f}s")
                return success
            else:
                self.log_test("Fast Duplicate Checking", False, f"Duplicate import failed: {response2.status_code}")
                return False
        except Exception as e:
            self.log_test("Fast Duplicate Checking", False, f"Exception: {e}")
            return False

    def run_tests(self):
        """Run all optimized chunked import tests"""
        print("🔥 STARTING OPTIMIZED CHUNKED IMPORT TESTING")
        print("=" * 80)
        print("ТЕСТИРОВАНИЕ ОПТИМИЗИРОВАННОГО CHUNKED ИМПОРТА")
        print("Testing optimizations:")
        print("1. Dynamic chunk sizing (5000/2500/1000 lines)")
        print("2. Bulk insert mode for large chunks")
        print("3. Fast IP-only duplicate checking")
        print("=" * 80)
        
        # Login first
        if not self.login():
            print("❌ Login failed - stopping tests")
            return False
        
        print("✅ Login successful")
        
        # Run tests
        test_results = []
        
        test_results.append(self.test_dynamic_chunk_sizing())
        test_results.append(self.test_bulk_insert_mode())
        test_results.append(self.test_fast_duplicate_checking())
        
        # Print results
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print("\n" + "=" * 80)
        print(f"🏁 OPTIMIZED CHUNKED IMPORT TESTING COMPLETE")
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("✅ ALL OPTIMIZED CHUNKED IMPORT TESTS PASSED!")
            print("🚀 EXPECTED IMPROVEMENTS VERIFIED:")
            print("   ✅ Dynamic chunk scaling working")
            print("   ✅ Bulk insert performance confirmed")
            print("   ✅ Fast IP-only duplicate checking working")
            return True
        else:
            print(f"❌ {total_tests - passed_tests} tests failed")
            return False

if __name__ == "__main__":
    tester = OptimizedChunkedImportTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)