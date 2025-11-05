#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

def test_local_backend():
    """Test local backend ping functionality"""
    print("🔥 TESTING LOCAL BACKEND PING FUNCTIONALITY")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    api_url = f"{base_url}/api"
    headers = {'Content-Type': 'application/json'}
    
    # Step 1: Login
    print("\n🔐 STEP 1: Authentication")
    login_data = {"username": "admin", "password": "admin"}
    
    try:
        login_response = requests.post(f"{api_url}/auth/login", json=login_data, headers=headers, timeout=10)
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            headers['Authorization'] = f'Bearer {token}'
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    # Step 2: Get database stats
    print("\n📊 STEP 2: Database Status Check")
    try:
        stats_response = requests.get(f"{api_url}/stats", headers=headers, timeout=10)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            total_nodes = stats.get('total', 0)
            not_tested = stats.get('not_tested', 0)
            ping_ok = stats.get('ping_ok', 0)
            ping_failed = stats.get('ping_failed', 0)
            
            print(f"   📈 Database State:")
            print(f"      Total Nodes: {total_nodes}")
            print(f"      Not Tested: {not_tested}")
            print(f"      Ping OK: {ping_ok}")
            print(f"      Ping Failed: {ping_failed}")
            
            if total_nodes == 0:
                print("   ❌ No nodes in database")
                return False
        else:
            print(f"   ❌ Stats failed: {stats_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Stats error: {e}")
        return False
    
    # Step 3: Get some nodes for testing
    print("\n🎯 STEP 3: Get Test Nodes")
    try:
        nodes_response = requests.get(f"{api_url}/nodes?limit=3", headers=headers, timeout=10)
        if nodes_response.status_code == 200:
            nodes_data = nodes_response.json()
            test_nodes = nodes_data.get('nodes', [])
            
            if not test_nodes:
                print("   ❌ No nodes available for testing")
                return False
            
            print(f"   📋 Selected {len(test_nodes)} nodes for testing:")
            for i, node in enumerate(test_nodes, 1):
                print(f"      {i}. Node {node['id']}: {node['ip']} (status: {node['status']})")
        else:
            print(f"   ❌ Get nodes failed: {nodes_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Get nodes error: {e}")
        return False
    
    # Step 4: Test individual ping
    print("\n🏓 STEP 4: Individual Ping Test")
    test_node = test_nodes[0]
    node_id = test_node['id']
    original_status = test_node['status']
    
    try:
        ping_data = {"node_ids": [node_id]}
        before_time = time.time()
        
        ping_response = requests.post(f"{api_url}/manual/ping-test", json=ping_data, headers=headers, timeout=30)
        
        after_time = time.time()
        duration = after_time - before_time
        
        if ping_response.status_code == 200:
            ping_result = ping_response.json()
            results = ping_result.get('results', [])
            
            if results:
                result = results[0]
                new_status = result.get('status')
                success = result.get('success', False)
                message = result.get('message', 'No message')
                
                print(f"   ✅ Ping Test Result:")
                print(f"      Node {node_id}: {original_status} → {new_status}")
                print(f"      Success: {success}")
                print(f"      Message: {message}")
                print(f"      Duration: {duration:.2f}s")
            else:
                print(f"   ❌ No results in ping response")
                return False
        else:
            print(f"   ❌ Ping test failed: {ping_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Ping test error: {e}")
        return False
    
    # Step 5: Test batch ping
    print("\n🚀 STEP 5: Batch Ping Test")
    batch_node_ids = [node['id'] for node in test_nodes[1:3]]  # Use remaining nodes
    
    if batch_node_ids:
        try:
            batch_data = {"node_ids": batch_node_ids}
            before_batch_time = time.time()
            
            batch_response = requests.post(f"{api_url}/manual/ping-test-batch", json=batch_data, headers=headers, timeout=60)
            
            after_batch_time = time.time()
            batch_duration = after_batch_time - before_batch_time
            
            if batch_response.status_code == 200:
                batch_result = batch_response.json()
                batch_results = batch_result.get('results', [])
                
                print(f"   ✅ Batch Ping Test Results:")
                print(f"      Duration: {batch_duration:.2f}s for {len(batch_node_ids)} nodes")
                
                for result in batch_results:
                    node_id = result.get('node_id')
                    status = result.get('status')
                    success = result.get('success', False)
                    print(f"      Node {node_id}: success={success}, status={status}")
            else:
                print(f"   ❌ Batch ping test failed: {batch_response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Batch ping test error: {e}")
            return False
    
    # Step 6: Verify database updates
    print("\n🗄️  STEP 6: Database Update Verification")
    time.sleep(2)  # Wait for database updates
    
    try:
        final_stats_response = requests.get(f"{api_url}/stats", headers=headers, timeout=10)
        if final_stats_response.status_code == 200:
            final_stats = final_stats_response.json()
            final_not_tested = final_stats.get('not_tested', 0)
            final_ping_ok = final_stats.get('ping_ok', 0)
            final_ping_failed = final_stats.get('ping_failed', 0)
            
            print(f"   📈 Final Database State:")
            print(f"      Not Tested: {not_tested} → {final_not_tested} (Change: {final_not_tested - not_tested})")
            print(f"      Ping OK: {ping_ok} → {final_ping_ok} (Change: {final_ping_ok - ping_ok})")
            print(f"      Ping Failed: {ping_failed} → {final_ping_failed} (Change: {final_ping_failed - ping_failed})")
            
            # Check if changes occurred
            status_changes = (final_not_tested != not_tested or 
                            final_ping_ok != ping_ok or 
                            final_ping_failed != ping_failed)
            
            if status_changes:
                print(f"      ✅ Status changes detected in database")
            else:
                print(f"      ⚠️  No status changes detected")
        else:
            print(f"   ❌ Final stats failed: {final_stats_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Final stats error: {e}")
        return False
    
    # Final assessment
    print(f"\n🎯 FINAL ASSESSMENT:")
    
    issues = []
    
    # Check performance
    if duration > 30:
        issues.append(f"Individual ping test too slow ({duration:.2f}s)")
    
    if 'batch_duration' in locals() and batch_duration > 60:
        issues.append(f"Batch ping test too slow ({batch_duration:.2f}s)")
    
    if not status_changes:
        issues.append("No database status changes detected")
    
    if issues:
        print(f"   ❌ ISSUES FOUND:")
        for issue in issues:
            print(f"      - {issue}")
        return False
    else:
        print(f"   ✅ ALL TESTS PASSED:")
        print(f"      - Individual ping test working ({duration:.2f}s)")
        if 'batch_duration' in locals():
            print(f"      - Batch ping test working ({batch_duration:.2f}s)")
        print(f"      - Database updates working correctly")
        print(f"      - No performance issues detected")
        return True

if __name__ == "__main__":
    success = test_local_backend()
    print(f"\n📊 TEST RESULT: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)