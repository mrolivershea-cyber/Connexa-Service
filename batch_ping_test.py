#!/usr/bin/env python3

import requests
import time
import json
from datetime import datetime

class BatchPingTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def login(self):
        """Login and get authentication token"""
        login_data = {"username": "admin", "password": "admin"}
        
        try:
            response = requests.post(f"{self.api_url}/auth/login", json=login_data, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                self.headers['Authorization'] = f'Bearer {self.token}'
                print("✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def create_test_nodes(self):
        """Create test nodes for batch ping testing"""
        working_ips = ["72.197.30.147", "100.11.102.204", "100.16.39.213"]
        non_working_ips = ["192.0.2.1", "192.0.2.2", "192.0.2.3", "192.0.2.4", "192.0.2.5"]
        
        created_nodes = []
        
        for i, ip in enumerate(working_ips + non_working_ips):
            node_data = {
                "ip": ip,
                "login": "admin",
                "password": "admin",
                "protocol": "pptp",
                "provider": "TestProvider",
                "country": "United States",
                "state": "California",
                "city": "Los Angeles",
                "comment": f"Batch ping test node {i+1}"
            }
            
            try:
                response = requests.post(f"{self.api_url}/nodes", json=node_data, headers=self.headers)
                if response.status_code == 200:
                    node = response.json()
                    created_nodes.append(node)
                    print(f"✅ Created test node {node['id']}: {ip}")
                else:
                    print(f"❌ Failed to create node {ip}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error creating node {ip}: {e}")
        
        return created_nodes

    def test_single_ping_performance(self, node_ids):
        """Test single node ping performance"""
        print(f"\n🏓 SINGLE NODE PING PERFORMANCE TEST")
        print("=" * 50)
        
        single_times = []
        
        for i, node_id in enumerate(node_ids[:3]):  # Test first 3 nodes
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{self.api_url}/manual/ping-test", 
                    json={"node_ids": [node_id]}, 
                    headers=self.headers
                )
                
                end_time = time.time()
                duration = end_time - start_time
                single_times.append(duration)
                
                if response.status_code == 200:
                    data = response.json()
                    result = data['results'][0] if data.get('results') else {}
                    message = result.get('message', 'No message')
                    print(f"   Node {node_id}: {duration:.2f}s - {message}")
                else:
                    print(f"   Node {node_id}: {duration:.2f}s - HTTP {response.status_code}")
                    
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                single_times.append(duration)
                print(f"   Node {node_id}: {duration:.2f}s - Error: {e}")
        
        avg_time = sum(single_times) / len(single_times) if single_times else 0
        print(f"   Average single node time: {avg_time:.2f}s")
        return avg_time

    def test_batch_ping_performance(self, node_ids):
        """Test batch ping performance"""
        print(f"\n🚀 BATCH PING PERFORMANCE TEST")
        print("=" * 50)
        
        batch_node_ids = node_ids[:10] if len(node_ids) >= 10 else node_ids
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.api_url}/manual/ping-test-batch", 
                json={"node_ids": batch_node_ids}, 
                headers=self.headers
            )
            
            end_time = time.time()
            batch_duration = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                successful_pings = sum(1 for r in results if r.get('success'))
                failed_pings = len(results) - successful_pings
                
                print(f"   Batch test duration: {batch_duration:.2f}s")
                print(f"   Nodes tested: {len(results)}")
                print(f"   Successful pings: {successful_pings}")
                print(f"   Failed pings: {failed_pings}")
                
                # Check fast mode indicators
                fast_mode_count = 0
                for result in results:
                    if 'ping_result' in result and result['ping_result']:
                        ping_result = result['ping_result']
                        avg_time = ping_result.get('avg_time', 0)
                        if avg_time == 0 or avg_time < 3000:  # Quick timeout or fast response
                            fast_mode_count += 1
                
                print(f"   Fast mode indicators: {fast_mode_count}/{len(results)}")
                
                # Check for database conflicts
                node_ids_in_results = [r.get('node_id') for r in results if 'node_id' in r]
                unique_node_ids = len(set(node_ids_in_results))
                
                print(f"   Unique node IDs: {unique_node_ids}/{len(batch_node_ids)}")
                
                return {
                    'duration': batch_duration,
                    'successful': successful_pings,
                    'failed': failed_pings,
                    'fast_mode_working': fast_mode_count > len(results) * 0.7,
                    'no_conflicts': unique_node_ids == len(batch_node_ids),
                    'results': results
                }
            else:
                print(f"   ❌ Batch ping failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            end_time = time.time()
            batch_duration = end_time - start_time
            print(f"   ❌ Batch ping error: {e}")
            print(f"   Duration: {batch_duration:.2f}s")
            return None

    def test_edge_cases(self):
        """Test edge cases"""
        print(f"\n🔍 EDGE CASES TEST")
        print("=" * 30)
        
        # Test empty list
        try:
            response = requests.post(
                f"{self.api_url}/manual/ping-test-batch", 
                json={"node_ids": []}, 
                headers=self.headers
            )
            empty_handled = response.status_code == 200 and len(response.json().get('results', [])) == 0
            print(f"   Empty list: {'✅' if empty_handled else '❌'}")
        except Exception as e:
            print(f"   Empty list: ❌ Error: {e}")
            empty_handled = False
        
        # Test invalid IDs
        try:
            response = requests.post(
                f"{self.api_url}/manual/ping-test-batch", 
                json={"node_ids": [99999, 99998]}, 
                headers=self.headers
            )
            invalid_handled = response.status_code == 200 and len(response.json().get('results', [])) == 0
            print(f"   Invalid IDs: {'✅' if invalid_handled else '❌'}")
        except Exception as e:
            print(f"   Invalid IDs: ❌ Error: {e}")
            invalid_handled = False
        
        return empty_handled and invalid_handled

    def cleanup_nodes(self, node_ids):
        """Delete test nodes"""
        if node_ids:
            try:
                response = requests.delete(
                    f"{self.api_url}/nodes", 
                    json={"node_ids": node_ids}, 
                    headers=self.headers
                )
                if response.status_code == 200:
                    print(f"🧹 Cleaned up {len(node_ids)} test nodes")
                else:
                    print(f"⚠️ Cleanup warning: HTTP {response.status_code}")
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")

    def run_batch_ping_tests(self):
        """Run comprehensive batch ping tests"""
        print("🔥 BATCH PING OPTIMIZATION TESTS")
        print("=" * 60)
        print(f"🌐 Testing against: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.login():
            return False
        
        # Create test nodes
        print(f"\n📋 CREATING TEST NODES")
        test_nodes = self.create_test_nodes()
        
        if len(test_nodes) < 5:
            print(f"❌ Insufficient test nodes created: {len(test_nodes)}")
            return False
        
        node_ids = [node['id'] for node in test_nodes]
        
        try:
            # Test single ping performance
            avg_single_time = self.test_single_ping_performance(node_ids)
            
            # Test batch ping performance
            batch_results = self.test_batch_ping_performance(node_ids)
            
            if batch_results:
                # Performance comparison
                estimated_sequential = avg_single_time * min(10, len(node_ids))
                actual_batch = batch_results['duration']
                improvement = ((estimated_sequential - actual_batch) / estimated_sequential) * 100 if estimated_sequential > 0 else 0
                
                print(f"\n📊 PERFORMANCE COMPARISON")
                print("=" * 40)
                print(f"   Estimated sequential time: {estimated_sequential:.2f}s")
                print(f"   Actual batch time: {actual_batch:.2f}s")
                print(f"   Performance improvement: {improvement:.1f}%")
                
                # Overall assessment
                performance_good = improvement > 30  # At least 30% improvement
                no_hanging = actual_batch < 60  # Should complete within 60 seconds
                some_success = batch_results['successful'] > 0
                
                print(f"\n🎯 ASSESSMENT")
                print("=" * 20)
                print(f"   Performance improvement: {'✅' if performance_good else '❌'} {improvement:.1f}%")
                print(f"   Fast mode working: {'✅' if batch_results['fast_mode_working'] else '❌'}")
                print(f"   No database conflicts: {'✅' if batch_results['no_conflicts'] else '❌'}")
                print(f"   No hanging/freezing: {'✅' if no_hanging else '❌'} ({actual_batch:.1f}s)")
                print(f"   Some successful pings: {'✅' if some_success else '❌'} ({batch_results['successful']})")
                
                # Test edge cases
                edge_cases_ok = self.test_edge_cases()
                print(f"   Edge cases handled: {'✅' if edge_cases_ok else '❌'}")
                
                overall_success = all([
                    performance_good,
                    batch_results['fast_mode_working'],
                    batch_results['no_conflicts'],
                    no_hanging,
                    some_success,
                    edge_cases_ok
                ])
                
                print(f"\n🏁 OVERALL RESULT: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
                
                return overall_success
            else:
                print(f"\n❌ Batch ping test failed")
                return False
                
        finally:
            # Cleanup
            self.cleanup_nodes(node_ids)

if __name__ == "__main__":
    tester = BatchPingTester()
    success = tester.run_batch_ping_tests()
    exit(0 if success else 1)