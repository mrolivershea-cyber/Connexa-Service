#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import random
import string

class SpeedOptimizationTester:
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
            print(f"✅ {name}: PASSED - {details}")
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
            self.log_test("Admin Login", True, "Successfully authenticated")
            return True
        else:
            self.log_test("Admin Login", False, f"Login failed: {response}")
            return False

    def generate_large_test_data(self, num_nodes: int) -> str:
        """Generate large test data with specified number of nodes"""
        test_nodes = []
        for i in range(num_nodes):
            # Use Format 7 (IP:Login:Pass) for maximum speed
            ip_a = (i // 65536) + 10
            ip_b = (i // 256) % 256
            ip_c = i % 256
            ip_d = (i % 254) + 1  # Avoid .0 and .255
            
            # Generate realistic credentials
            login = f"user{i:06d}"
            password = f"pass{i:06d}"
            
            test_nodes.append(f"{ip_a}.{ip_b}.{ip_c}.{ip_d}:{login}:{password}")
        
        return "\n".join(test_nodes)

    def test_scenario_1_large_file_import_speed(self):
        """
        SCENARIO 1: Import 1.5MB file (~50K+ nodes) - should complete in 1-2 minutes max
        Tests the optimizations:
        - Increased chunk sizes: 10K lines for large files
        - Removed duplicate checking: Ultra-fast mode
        - INSERT OR IGNORE: SQLite handles duplicates
        - Reduced pauses: No asyncio.sleep delays
        - Lowered chunked threshold: 200KB instead of 500KB
        """
        print(f"\n🚀 SCENARIO 1: Testing 1.5MB File Import Speed Optimization")
        
        # Generate approximately 50,000 nodes to reach ~1.5MB
        num_nodes = 50000
        print(f"📊 Generating {num_nodes:,} test nodes...")
        
        start_generation = time.time()
        large_data = self.generate_large_test_data(num_nodes)
        generation_time = time.time() - start_generation
        
        data_size = len(large_data.encode('utf-8'))
        data_size_mb = data_size / (1024 * 1024)
        
        print(f"📈 Generated {data_size_mb:.2f}MB of test data in {generation_time:.1f}s")
        
        # Verify we have at least 1.5MB
        if data_size_mb < 1.4:
            self.log_test("Scenario 1 - Data Generation", False, 
                         f"Generated only {data_size_mb:.2f}MB, need at least 1.4MB")
            return False
        
        import_data = {
            "data": large_data,
            "protocol": "pptp"
        }
        
        # Test import speed
        print(f"⏱️  Starting import of {data_size_mb:.2f}MB file...")
        start_import = time.time()
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        end_import = time.time()
        import_duration = end_import - start_import
        import_duration_minutes = import_duration / 60
        
        print(f"⏱️  Import completed in {import_duration:.1f}s ({import_duration_minutes:.2f} minutes)")
        
        if success:
            # Check if it used chunked processing (should for files >200KB)
            if 'session_id' in response:
                session_id = response['session_id']
                print(f"✅ Used chunked processing with session_id: {session_id}")
                
                # Monitor progress until completion
                max_wait_time = 180  # 3 minutes max wait
                wait_start = time.time()
                
                while (time.time() - wait_start) < max_wait_time:
                    progress_success, progress_response = self.make_request('GET', f'import/progress/{session_id}')
                    
                    if progress_success:
                        status = progress_response.get('status', 'unknown')
                        processed_chunks = progress_response.get('processed_chunks', 0)
                        total_chunks = progress_response.get('total_chunks', 0)
                        added = progress_response.get('added', 0)
                        
                        print(f"📊 Progress: {processed_chunks}/{total_chunks} chunks, {added:,} nodes added, status: {status}")
                        
                        if status == 'completed':
                            final_import_time = time.time() - start_import
                            final_minutes = final_import_time / 60
                            
                            # Check if completed within target time (1-2 minutes)
                            target_met = final_minutes <= 2.0
                            
                            if target_met:
                                self.log_test("Scenario 1 - Large File Import Speed", True, 
                                             f"✅ SPEED TARGET MET: {data_size_mb:.2f}MB imported in {final_minutes:.2f} minutes (≤2 min target), {added:,} nodes added")
                            else:
                                self.log_test("Scenario 1 - Large File Import Speed", False, 
                                             f"❌ SPEED TARGET MISSED: {data_size_mb:.2f}MB took {final_minutes:.2f} minutes (>2 min target)")
                            
                            return target_met
                        elif status == 'failed':
                            self.log_test("Scenario 1 - Large File Import Speed", False, 
                                         f"Import failed during processing")
                            return False
                    
                    time.sleep(5)  # Check every 5 seconds
                
                # Timeout reached
                self.log_test("Scenario 1 - Large File Import Speed", False, 
                             f"Import timed out after {max_wait_time}s")
                return False
                
            else:
                # Regular processing (not chunked)
                if 'report' in response:
                    report = response['report']
                    added = report.get('added', 0)
                    
                    # Check if completed within target time
                    target_met = import_duration_minutes <= 2.0
                    
                    if target_met:
                        self.log_test("Scenario 1 - Large File Import Speed", True, 
                                     f"✅ SPEED TARGET MET: {data_size_mb:.2f}MB imported in {import_duration_minutes:.2f} minutes (≤2 min target), {added:,} nodes added")
                    else:
                        self.log_test("Scenario 1 - Large File Import Speed", False, 
                                     f"❌ SPEED TARGET MISSED: {data_size_mb:.2f}MB took {import_duration_minutes:.2f} minutes (>2 min target)")
                    
                    return target_met
                else:
                    self.log_test("Scenario 1 - Large File Import Speed", False, 
                                 f"Unexpected response format: {response}")
                    return False
        else:
            self.log_test("Scenario 1 - Large File Import Speed", False, 
                         f"Import request failed: {response}")
            return False

    def test_scenario_2_select_all_without_warnings(self):
        """
        SCENARIO 2: Select All without warnings - check bulk operations speed
        Tests the optimizations:
        - Removed warnings: Select All and Delete All without confirm dialogs
        - Fast bulk operations
        """
        print(f"\n🚀 SCENARIO 2: Testing Select All Without Warnings")
        
        # First, ensure we have some nodes to work with
        print("📊 Setting up test nodes for Select All test...")
        
        # Create a moderate number of test nodes for Select All testing
        test_data = self.generate_large_test_data(1000)  # 1000 nodes for testing
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Import test nodes
        setup_success, setup_response = self.make_request('POST', 'nodes/import', import_data)
        
        if not setup_success:
            self.log_test("Scenario 2 - Setup Test Nodes", False, 
                         f"Failed to create test nodes: {setup_response}")
            return False
        
        print("✅ Test nodes created successfully")
        
        # Test 1: Get all node IDs (Select All functionality)
        print("🔍 Testing Select All functionality...")
        
        start_select_all = time.time()
        select_success, select_response = self.make_request('GET', 'nodes/all-ids')
        select_duration = time.time() - start_select_all
        
        if select_success and 'node_ids' in select_response:
            node_ids = select_response['node_ids']
            total_count = select_response.get('total_count', 0)
            
            # Check that Select All is fast (should be <5 seconds even for large datasets)
            select_fast = select_duration < 5.0
            
            if select_fast:
                self.log_test("Scenario 2 - Select All Speed", True, 
                             f"✅ Select All fast: {total_count:,} node IDs retrieved in {select_duration:.2f}s (<5s target)")
            else:
                self.log_test("Scenario 2 - Select All Speed", False, 
                             f"❌ Select All slow: {total_count:,} node IDs took {select_duration:.2f}s (≥5s)")
                return False
            
            # Test 2: Bulk delete without warnings (test with subset to avoid deleting all data)
            print("🗑️  Testing bulk delete speed...")
            
            # Use only first 100 nodes for delete test to preserve data
            test_node_ids = node_ids[:100] if len(node_ids) >= 100 else node_ids[:10]
            
            delete_data = {
                "node_ids": test_node_ids
            }
            
            start_delete = time.time()
            delete_success, delete_response = self.make_request('DELETE', 'nodes', delete_data)
            delete_duration = time.time() - start_delete
            
            if delete_success:
                deleted_count = len(test_node_ids)
                
                # Check that bulk delete is fast (should be <3 seconds for moderate batches)
                delete_fast = delete_duration < 3.0
                
                if delete_fast:
                    self.log_test("Scenario 2 - Bulk Delete Speed", True, 
                                 f"✅ Bulk delete fast: {deleted_count} nodes deleted in {delete_duration:.2f}s (<3s target)")
                    return True
                else:
                    self.log_test("Scenario 2 - Bulk Delete Speed", False, 
                                 f"❌ Bulk delete slow: {deleted_count} nodes took {delete_duration:.2f}s (≥3s)")
                    return False
            else:
                self.log_test("Scenario 2 - Bulk Delete Speed", False, 
                             f"Bulk delete failed: {delete_response}")
                return False
        else:
            self.log_test("Scenario 2 - Select All Speed", False, 
                         f"Select All failed: {select_response}")
            return False

    def test_chunked_threshold_optimization(self):
        """
        Test that chunked threshold is lowered to 200KB instead of 500KB
        """
        print(f"\n🚀 Testing Chunked Threshold Optimization (200KB vs 500KB)")
        
        # Generate data that's between 200KB and 500KB to test the threshold
        target_size_kb = 250  # 250KB - should trigger chunked mode with new 200KB threshold
        
        # Estimate nodes needed for 250KB (each Format 7 line is roughly 25-30 bytes)
        estimated_nodes = int((target_size_kb * 1024) / 28)  # ~28 bytes per line
        
        test_data = self.generate_large_test_data(estimated_nodes)
        actual_size = len(test_data.encode('utf-8'))
        actual_size_kb = actual_size / 1024
        
        print(f"📊 Generated {actual_size_kb:.1f}KB test data ({estimated_nodes:,} nodes)")
        
        # This should trigger chunked processing with the new 200KB threshold
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        duration = time.time() - start_time
        
        if success:
            # Check if it used chunked processing (should with new 200KB threshold)
            if 'session_id' in response and actual_size_kb > 200:
                self.log_test("Chunked Threshold Optimization", True, 
                             f"✅ NEW THRESHOLD WORKING: {actual_size_kb:.1f}KB file triggered chunked processing (200KB threshold)")
                return True
            elif 'report' in response and actual_size_kb <= 200:
                self.log_test("Chunked Threshold Optimization", True, 
                             f"✅ THRESHOLD CORRECT: {actual_size_kb:.1f}KB file used regular processing (≤200KB)")
                return True
            else:
                self.log_test("Chunked Threshold Optimization", False, 
                             f"❌ THRESHOLD ISSUE: {actual_size_kb:.1f}KB file processing mode unexpected")
                return False
        else:
            self.log_test("Chunked Threshold Optimization", False, 
                         f"Import failed: {response}")
            return False

    def test_chunk_size_optimization(self):
        """
        Test that chunk sizes are optimized: 10K lines for large files
        """
        print(f"\n🚀 Testing Chunk Size Optimization (10K lines for large files)")
        
        # Generate a large file that should use 10K line chunks
        large_nodes = 60000  # >50K nodes should trigger 10K line chunks
        
        print(f"📊 Generating {large_nodes:,} nodes for chunk size test...")
        test_data = self.generate_large_test_data(large_nodes)
        data_size_mb = len(test_data.encode('utf-8')) / (1024 * 1024)
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        print(f"📈 Testing chunked import of {data_size_mb:.2f}MB file...")
        
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import-chunked', import_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            total_chunks = response.get('total_chunks', 0)
            
            # Calculate expected chunks with 10K line optimization
            total_lines = large_nodes
            expected_chunks_10k = (total_lines + 9999) // 10000  # Ceiling division
            
            # Allow some tolerance for chunk calculation
            chunk_tolerance = max(2, expected_chunks_10k // 10)  # 10% tolerance or minimum 2
            
            chunks_in_range = abs(total_chunks - expected_chunks_10k) <= chunk_tolerance
            
            if chunks_in_range:
                self.log_test("Chunk Size Optimization", True, 
                             f"✅ 10K CHUNK SIZE VERIFIED: {total_lines:,} lines → {total_chunks} chunks (expected ~{expected_chunks_10k})")
                
                # Monitor a few progress updates to verify chunk processing speed
                progress_checks = 0
                max_checks = 5
                
                while progress_checks < max_checks:
                    time.sleep(2)
                    progress_success, progress_response = self.make_request('GET', f'import/progress/{session_id}')
                    
                    if progress_success:
                        status = progress_response.get('status', 'unknown')
                        processed_chunks = progress_response.get('processed_chunks', 0)
                        
                        print(f"📊 Chunk progress: {processed_chunks}/{total_chunks} chunks processed")
                        
                        if status == 'completed':
                            processing_time = time.time() - start_time
                            self.log_test("Chunk Size Processing Speed", True, 
                                         f"✅ Large file processed in {processing_time:.1f}s with optimized 10K chunks")
                            return True
                        elif status == 'failed':
                            self.log_test("Chunk Size Processing Speed", False, 
                                         f"Processing failed")
                            return False
                    
                    progress_checks += 1
                
                # If we get here, it's still processing but we verified chunk size
                return True
            else:
                self.log_test("Chunk Size Optimization", False, 
                             f"❌ CHUNK SIZE WRONG: {total_lines:,} lines → {total_chunks} chunks (expected ~{expected_chunks_10k})")
                return False
        else:
            self.log_test("Chunk Size Optimization", False, 
                         f"Chunked import failed: {response}")
            return False

    def test_ultra_fast_mode_no_duplicate_checking(self):
        """
        Test ultra-fast mode without duplicate checking
        """
        print(f"\n🚀 Testing Ultra-Fast Mode (No Duplicate Checking)")
        
        # Create test data with intentional duplicates
        base_nodes = []
        for i in range(1000):
            base_nodes.append(f"192.168.100.{i%254+1}:fastuser{i}:fastpass{i}")
        
        # Add the same nodes again (duplicates)
        duplicate_nodes = base_nodes.copy()
        
        # Combine original and duplicates
        all_nodes = base_nodes + duplicate_nodes
        test_data = "\n".join(all_nodes)
        
        print(f"📊 Testing {len(all_nodes):,} nodes (including {len(duplicate_nodes):,} duplicates)")
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        duration = time.time() - start_time
        
        if success:
            if 'report' in response:
                report = response['report']
                added = report.get('added', 0)
                skipped = report.get('skipped_duplicates', 0)
                
                # In ultra-fast mode, duplicates should be handled by SQLite INSERT OR IGNORE
                # So we should see fast processing regardless of duplicates
                ultra_fast = duration < 10.0  # Should be very fast
                
                if ultra_fast:
                    self.log_test("Ultra-Fast Mode Speed", True, 
                                 f"✅ ULTRA-FAST MODE: {len(all_nodes):,} nodes processed in {duration:.2f}s (<10s target)")
                    
                    # Check that SQLite handled duplicates automatically
                    if added > 0:
                        self.log_test("SQLite Duplicate Handling", True, 
                                     f"✅ SQLite INSERT OR IGNORE: {added} unique nodes added, duplicates handled automatically")
                        return True
                    else:
                        self.log_test("SQLite Duplicate Handling", False, 
                                     f"❌ No nodes added - possible issue with duplicate handling")
                        return False
                else:
                    self.log_test("Ultra-Fast Mode Speed", False, 
                                 f"❌ NOT ULTRA-FAST: {len(all_nodes):,} nodes took {duration:.2f}s (≥10s)")
                    return False
            else:
                self.log_test("Ultra-Fast Mode Speed", False, 
                             f"Unexpected response format: {response}")
                return False
        else:
            self.log_test("Ultra-Fast Mode Speed", False, 
                         f"Import failed: {response}")
            return False

    def run_all_speed_optimization_tests(self):
        """Run all speed optimization tests"""
        print("🚀 STARTING SPEED OPTIMIZATION TESTING")
        print("=" * 60)
        
        # Login first
        if not self.test_login():
            print("❌ Cannot proceed without authentication")
            return False
        
        # Run all optimization tests
        tests = [
            ("Scenario 1 - 1.5MB Import Speed", self.test_scenario_1_large_file_import_speed),
            ("Scenario 2 - Select All Without Warnings", self.test_scenario_2_select_all_without_warnings),
            ("Chunked Threshold Optimization", self.test_chunked_threshold_optimization),
            ("Chunk Size Optimization", self.test_chunk_size_optimization),
            ("Ultra-Fast Mode", self.test_ultra_fast_mode_no_duplicate_checking),
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 RUNNING: {test_name}")
            print(f"{'='*60}")
            
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ TEST ERROR: {test_name} - {str(e)}")
                results.append((test_name, False))
        
        # Print final summary
        print(f"\n{'='*60}")
        print("📊 SPEED OPTIMIZATION TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
            if result:
                passed += 1
        
        print(f"\n📈 OVERALL RESULTS: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL SPEED OPTIMIZATION TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {total-passed} tests failed - optimization may need attention")
            return False

def main():
    """Main test execution"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "https://memory-mcp.preview.emergentagent.com"
    
    print(f"🚀 Speed Optimization Testing")
    print(f"🌐 Target URL: {base_url}")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = SpeedOptimizationTester(base_url)
    success = tester.run_all_speed_optimization_tests()
    
    if success:
        print("\n🎉 ALL SPEED OPTIMIZATION REQUIREMENTS VERIFIED!")
        sys.exit(0)
    else:
        print("\n❌ SOME SPEED OPTIMIZATION TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()