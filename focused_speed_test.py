#!/usr/bin/env python3

import requests
import time
import json
from datetime import datetime

class FocusedSpeedTester:
    def __init__(self):
        self.base_url = "https://memory-mcp.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def login(self):
        """Login and get token"""
        login_data = {"username": "admin", "password": "admin"}
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.headers['Authorization'] = f'Bearer {self.token}'
                print("✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def test_chunked_threshold_200kb(self):
        """Test that files >200KB trigger chunked processing (was 500KB)"""
        print("\n🧪 Testing Chunked Threshold Optimization (200KB)")
        
        # Generate ~250KB of data (should trigger chunked with new 200KB threshold)
        lines = []
        for i in range(8500):  # ~250KB
            lines.append(f"10.0.{i//256}.{i%256}:user{i}:pass{i}")
        
        test_data = "\n".join(lines)
        data_size_kb = len(test_data.encode('utf-8')) / 1024
        
        print(f"📊 Generated {data_size_kb:.1f}KB test data")
        
        import_data = {"data": test_data, "protocol": "pptp"}
        
        try:
            response = requests.post(f"{self.api_url}/nodes/import", json=import_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'session_id' in result:
                    print(f"✅ CHUNKED THRESHOLD WORKING: {data_size_kb:.1f}KB triggered chunked processing")
                    return True, result.get('session_id')
                else:
                    print(f"❌ CHUNKED THRESHOLD ISSUE: {data_size_kb:.1f}KB did not trigger chunked processing")
                    return False, None
            else:
                print(f"❌ Import failed: {response.status_code}")
                return False, None
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False, None

    def test_chunk_size_10k_lines(self):
        """Test that large files use 10K line chunks (was 5K)"""
        print("\n🧪 Testing Chunk Size Optimization (10K lines)")
        
        # Generate >50K lines to trigger 10K chunk size
        lines = []
        for i in range(55000):  # >50K lines
            lines.append(f"172.16.{i//256}.{i%256}:bulk{i}:pass{i}")
        
        test_data = "\n".join(lines)
        data_size_mb = len(test_data.encode('utf-8')) / (1024 * 1024)
        
        print(f"📊 Generated {data_size_mb:.2f}MB test data ({len(lines):,} lines)")
        
        import_data = {"data": test_data, "protocol": "pptp"}
        
        try:
            response = requests.post(f"{self.api_url}/nodes/import-chunked", json=import_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                total_chunks = result.get('total_chunks', 0)
                
                # With 10K line chunks, 55K lines should be ~6 chunks
                expected_chunks = (len(lines) + 9999) // 10000  # Ceiling division
                
                if abs(total_chunks - expected_chunks) <= 1:  # Allow 1 chunk tolerance
                    print(f"✅ CHUNK SIZE OPTIMIZED: {len(lines):,} lines → {total_chunks} chunks (~10K per chunk)")
                    return True, result.get('session_id')
                else:
                    print(f"❌ CHUNK SIZE WRONG: {len(lines):,} lines → {total_chunks} chunks (expected ~{expected_chunks})")
                    return False, None
            else:
                print(f"❌ Chunked import failed: {response.status_code}")
                return False, None
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False, None

    def test_select_all_speed(self):
        """Test Select All functionality speed (no warnings)"""
        print("\n🧪 Testing Select All Speed (No Warnings)")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_url}/nodes/all-ids", headers=self.headers)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                node_count = result.get('total_count', 0)
                
                # Should be fast even for large datasets
                if duration < 5.0:
                    print(f"✅ SELECT ALL FAST: {node_count:,} node IDs retrieved in {duration:.2f}s")
                    return True, node_count
                else:
                    print(f"❌ SELECT ALL SLOW: {node_count:,} node IDs took {duration:.2f}s")
                    return False, node_count
            else:
                print(f"❌ Select All failed: {response.status_code}")
                return False, 0
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False, 0

    def test_bulk_delete_speed(self):
        """Test bulk delete speed (no warnings)"""
        print("\n🧪 Testing Bulk Delete Speed (No Warnings)")
        
        # First create some test nodes
        test_lines = []
        for i in range(100):
            test_lines.append(f"203.0.113.{i}:deltest{i}:pass{i}")
        
        test_data = "\n".join(test_lines)
        import_data = {"data": test_data, "protocol": "pptp"}
        
        try:
            # Create test nodes
            response = requests.post(f"{self.api_url}/nodes/import", json=import_data, headers=self.headers)
            
            if response.status_code != 200:
                print(f"❌ Failed to create test nodes: {response.status_code}")
                return False
            
            # Get the created node IDs
            response = requests.get(f"{self.api_url}/nodes?ip=203.0.113", headers=self.headers)
            
            if response.status_code == 200:
                nodes_data = response.json()
                nodes = nodes_data.get('nodes', [])
                
                if len(nodes) >= 10:  # Use first 10 for delete test
                    node_ids = [node['id'] for node in nodes[:10]]
                    
                    delete_data = {"node_ids": node_ids}
                    
                    start_time = time.time()
                    response = requests.delete(f"{self.api_url}/nodes", json=delete_data, headers=self.headers)
                    duration = time.time() - start_time
                    
                    if response.status_code == 200:
                        if duration < 3.0:
                            print(f"✅ BULK DELETE FAST: {len(node_ids)} nodes deleted in {duration:.2f}s")
                            return True
                        else:
                            print(f"❌ BULK DELETE SLOW: {len(node_ids)} nodes took {duration:.2f}s")
                            return False
                    else:
                        print(f"❌ Bulk delete failed: {response.status_code}")
                        return False
                else:
                    print(f"❌ Not enough test nodes created: {len(nodes)}")
                    return False
            else:
                print(f"❌ Failed to retrieve test nodes: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False

    def monitor_import_progress(self, session_id, max_wait_minutes=3):
        """Monitor import progress and measure completion time"""
        print(f"⏱️  Monitoring import progress for session: {session_id}")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while (time.time() - start_time) < max_wait_seconds:
            try:
                response = requests.get(f"{self.api_url}/import/progress/{session_id}", headers=self.headers)
                
                if response.status_code == 200:
                    progress = response.json()
                    status = progress.get('status', 'unknown')
                    processed_chunks = progress.get('processed_chunks', 0)
                    total_chunks = progress.get('total_chunks', 0)
                    added = progress.get('added', 0)
                    
                    print(f"📊 Progress: {processed_chunks}/{total_chunks} chunks, {added:,} nodes added, status: {status}")
                    
                    if status == 'completed':
                        total_time = time.time() - start_time
                        total_minutes = total_time / 60
                        
                        print(f"✅ Import completed in {total_minutes:.2f} minutes")
                        return True, total_minutes, added
                    elif status == 'failed':
                        print(f"❌ Import failed")
                        return False, 0, 0
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"❌ Progress check error: {e}")
                break
        
        print(f"❌ Import timed out after {max_wait_minutes} minutes")
        return False, 0, 0

    def run_focused_tests(self):
        """Run focused speed optimization tests"""
        print("🚀 FOCUSED SPEED OPTIMIZATION TESTING")
        print("=" * 50)
        print(f"🌐 Target: {self.base_url}")
        print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        if not self.login():
            print("❌ Cannot proceed without authentication")
            return False
        
        results = []
        
        # Test 1: Chunked threshold optimization
        print("\n" + "="*50)
        success, session_id = self.test_chunked_threshold_200kb()
        results.append(("Chunked Threshold 200KB", success))
        
        # Test 2: Chunk size optimization
        print("\n" + "="*50)
        success, large_session_id = self.test_chunk_size_10k_lines()
        results.append(("Chunk Size 10K Lines", success))
        
        # Test 3: Select All speed
        print("\n" + "="*50)
        success, node_count = self.test_select_all_speed()
        results.append(("Select All Speed", success))
        
        # Test 4: Bulk delete speed
        print("\n" + "="*50)
        success = self.test_bulk_delete_speed()
        results.append(("Bulk Delete Speed", success))
        
        # Test 5: Monitor large import completion time
        if large_session_id:
            print("\n" + "="*50)
            print("🧪 Testing Large Import Completion Time")
            success, minutes, added = self.monitor_import_progress(large_session_id, max_wait_minutes=3)
            
            if success and minutes <= 2.0:
                print(f"✅ SPEED TARGET MET: Large import completed in {minutes:.2f} minutes (≤2 min target)")
                results.append(("Large Import Speed", True))
            elif success:
                print(f"⚠️  SPEED TARGET MISSED: Large import took {minutes:.2f} minutes (>2 min target)")
                results.append(("Large Import Speed", False))
            else:
                print(f"❌ Large import failed or timed out")
                results.append(("Large Import Speed", False))
        
        # Print summary
        print("\n" + "="*50)
        print("📊 FOCUSED TEST RESULTS SUMMARY")
        print("="*50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
            if result:
                passed += 1
        
        print(f"\n📈 OVERALL: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL SPEED OPTIMIZATIONS VERIFIED!")
            return True
        else:
            print(f"⚠️  {total-passed} optimizations need attention")
            return False

def main():
    tester = FocusedSpeedTester()
    success = tester.run_focused_tests()
    
    if success:
        print("\n🎉 SPEED OPTIMIZATION TESTING COMPLETE - ALL PASSED!")
    else:
        print("\n⚠️  SPEED OPTIMIZATION TESTING COMPLETE - SOME ISSUES FOUND")
    
    return success

if __name__ == "__main__":
    main()