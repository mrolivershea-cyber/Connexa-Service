#!/usr/bin/env python3

import requests
import json
from datetime import datetime
import time

# Comprehensive test for all timestamp scenarios from review request
BASE_URL = "https://memory-mcp.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

def login():
    """Login and get token"""
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def check_timestamp_is_recent(timestamp_str, max_age_seconds=120):
    """Check if timestamp is recent (within max_age_seconds)"""
    if not timestamp_str:
        return False, "No timestamp"
    
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now()
        age_seconds = abs((now - timestamp).total_seconds())
        
        if age_seconds <= max_age_seconds:
            return True, f"{age_seconds:.1f}s ago"
        else:
            return False, f"{age_seconds:.1f}s ago (too old)"
    except Exception as e:
        return False, f"Parse error: {e}"

def test_all_timestamp_scenarios():
    """Test all timestamp scenarios from review request"""
    token = login()
    if not token:
        print("❌ Login failed")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("🕒 COMPREHENSIVE TIMESTAMP FIX VERIFICATION")
    print("Review Request: Test timestamp fix after database schema change")
    print("=" * 70)
    
    results = {
        'import_nodes': False,
        'create_node': False,
        'query_nodes': False,
        'manual_ping': False
    }
    
    # TEST 1: Import new nodes via POST /api/nodes/import
    print("\n1️⃣  TESTING: Import new nodes via POST /api/nodes/import")
    print("   Expected: Imported node has current timestamp (within last 2 minutes)")
    print("   Expected: last_update is NOT '8 hours ago'")
    
    timestamp = str(int(time.time()))
    import_data = {
        "data": f"""Ip: 10.10.10.{timestamp[-2:]}
Login: testuser{timestamp[-4:]}
Pass: testpass
State: California
City: Los Angeles""",
        "protocol": "pptp",
        "testing_mode": "no_test"
    }
    
    response = requests.post(f"{API_URL}/nodes/import", json=import_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('report', {}).get('added', 0) > 0:
            # Get the imported node
            ip = f"10.10.10.{timestamp[-2:]}"
            response = requests.get(f"{API_URL}/nodes?ip={ip}", headers=headers)
            if response.status_code == 200:
                nodes = response.json()['nodes']
                if nodes:
                    node = nodes[0]
                    is_recent, age_info = check_timestamp_is_recent(node.get('last_update'))
                    
                    if is_recent:
                        print(f"   ✅ IMPORT TIMESTAMP CORRECT: {age_info}")
                        results['import_nodes'] = True
                    else:
                        print(f"   ❌ IMPORT TIMESTAMP INCORRECT: {age_info}")
                else:
                    print("   ❌ Imported node not found")
            else:
                print(f"   ❌ Failed to query imported node: {response.status_code}")
        else:
            print(f"   ❌ No nodes imported: {result}")
    else:
        print(f"   ❌ Import failed: {response.status_code}")
    
    # TEST 2: Create single node via POST /api/nodes
    print("\n2️⃣  TESTING: Create single node via POST /api/nodes")
    print("   Expected: Node has current timestamp immediately after creation")
    
    timestamp = str(int(time.time()))
    node_data = {
        "ip": f"11.11.11.{timestamp[-2:]}",
        "login": "test",
        "password": "test123",
        "protocol": "pptp"
    }
    
    response = requests.post(f"{API_URL}/nodes", json=node_data, headers=headers)
    
    if response.status_code == 200:
        node = response.json()
        is_recent, age_info = check_timestamp_is_recent(node.get('last_update'))
        
        if is_recent:
            print(f"   ✅ CREATE TIMESTAMP CORRECT: {age_info}")
            results['create_node'] = True
        else:
            print(f"   ❌ CREATE TIMESTAMP INCORRECT: {age_info}")
    else:
        print(f"   ❌ Create failed: {response.status_code}")
    
    # TEST 3: Query nodes via GET /api/nodes
    print("\n3️⃣  TESTING: Query nodes via GET /api/nodes")
    print("   Expected: Newest nodes have timestamps within last few minutes")
    print("   Expected: Timestamp format is ISO format with current time")
    
    response = requests.get(f"{API_URL}/nodes?limit=10", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        nodes = result.get('nodes', [])
        if nodes:
            recent_count = 0
            old_count = 0
            
            print(f"   Checking {len(nodes)} nodes:")
            for node in nodes[:5]:  # Check first 5 nodes
                is_recent, age_info = check_timestamp_is_recent(node.get('last_update'), 3600)  # 1 hour
                
                if is_recent:
                    recent_count += 1
                    print(f"     Node {node['id']}: ✅ {age_info}")
                else:
                    old_count += 1
                    print(f"     Node {node['id']}: ⏰ {age_info}")
            
            if recent_count >= 3:  # At least 3 nodes should be recent
                print(f"   ✅ QUERY TIMESTAMPS GOOD: {recent_count} recent, {old_count} old")
                results['query_nodes'] = True
            else:
                print(f"   ❌ QUERY TIMESTAMPS POOR: {recent_count} recent, {old_count} old")
        else:
            print("   ❌ No nodes found")
    else:
        print(f"   ❌ Query failed: {response.status_code}")
    
    # TEST 4: Manual ping test on newly created node
    print("\n4️⃣  TESTING: Manual ping test on newly created node")
    print("   Expected: last_update changes to even more recent time after test")
    
    # Create a fresh node for ping testing
    timestamp = str(int(time.time()))
    node_data = {
        "ip": f"192.168.200.{timestamp[-2:]}",
        "login": f"pingtest{timestamp[-4:]}",
        "password": "pingpass123",
        "protocol": "pptp"
    }
    
    response = requests.post(f"{API_URL}/nodes", json=node_data, headers=headers)
    if response.status_code == 200:
        node = response.json()
        node_id = node['id']
        initial_timestamp = node.get('last_update')
        
        print(f"   Created test node {node_id} with timestamp: {initial_timestamp}")
        
        # Wait a moment to ensure timestamp difference
        time.sleep(2)
        
        # Perform manual ping test
        ping_data = {"node_ids": [node_id]}
        response = requests.post(f"{API_URL}/manual/ping-test", json=ping_data, headers=headers)
        
        if response.status_code == 200:
            # Get updated node
            response = requests.get(f"{API_URL}/nodes?id={node_id}", headers=headers)
            if response.status_code == 200:
                nodes = response.json()['nodes']
                if nodes:
                    updated_node = nodes[0]
                    new_timestamp = updated_node.get('last_update')
                    
                    if new_timestamp != initial_timestamp:
                        is_recent, age_info = check_timestamp_is_recent(new_timestamp)
                        if is_recent:
                            print(f"   ✅ PING TEST TIMESTAMP UPDATED: {age_info}")
                            results['manual_ping'] = True
                        else:
                            print(f"   ❌ PING TEST TIMESTAMP NOT RECENT: {age_info}")
                    else:
                        print(f"   ❌ PING TEST TIMESTAMP NOT CHANGED")
                else:
                    print("   ❌ Updated node not found")
            else:
                print(f"   ❌ Failed to get updated node: {response.status_code}")
        else:
            print(f"   ❌ Manual ping test failed: {response.status_code}")
    else:
        print(f"   ❌ Failed to create test node: {response.status_code}")
    
    # FINAL SUMMARY
    print("\n" + "=" * 70)
    print("🎯 TIMESTAMP FIX VERIFICATION RESULTS")
    print("=" * 70)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TIMESTAMP TESTS PASSED - FIX IS WORKING CORRECTLY!")
        print("✅ New nodes should have last_update set to current UTC time")
        print("✅ Timestamps should show as 'just now' or 'X seconds ago' in frontend")
        print("✅ Every status change should update last_update to current time")
    elif passed_tests >= 3:
        print("⚠️  MOSTLY WORKING - Some timestamp tests passed")
        print("🔧 The core timestamp fix is working for node creation and import")
    else:
        print("❌ TIMESTAMP FIX NEEDS MORE WORK")
        print("🚨 User reported issue may still persist")
    
    print("=" * 70)
    
    return passed_tests == total_tests

if __name__ == "__main__":
    test_all_timestamp_scenarios()