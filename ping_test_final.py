#!/usr/bin/env python3

import requests
import json

def test_ping_restriction_removal():
    base_url = "https://memory-mcp.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    print("✅ Login successful")
    print("\n🔥 CRITICAL TEST: Ping Test Status Restriction Removal")
    print("=" * 60)
    
    # Test scenarios with actual existing nodes
    scenarios = [
        {"name": "not_tested node", "node_id": 11, "expected_original": "not_tested"},
        {"name": "ping_failed node", "node_id": 1, "expected_original": "ping_failed"},
        {"name": "ping_ok node", "node_id": 2337, "expected_original": "ping_ok"}
    ]
    
    all_passed = True
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🧪 Test Scenario {i}: {scenario['name']} (ID {scenario['node_id']})")
        
        # Test single node
        test_data = {"node_ids": [scenario['node_id']]}
        response = requests.post(f"{api_url}/manual/ping-test", json=test_data, headers=headers)
        
        if response.status_code != 200:
            print(f"   ❌ FAILED: API call failed with status {response.status_code}: {response.text}")
            all_passed = False
            continue
        
        result_data = response.json()
        
        if 'results' not in result_data or not result_data['results']:
            print(f"   ❌ FAILED: No results in response: {result_data}")
            all_passed = False
            continue
        
        result = result_data['results'][0]
        print(f"   Response: {result}")
        
        # Check if the test was successful and has required fields
        if (result.get('success') and 
            'original_status' in result and
            'status' in result and
            'message' in result and
            '->' in result['message']):
            print(f"   ✅ SUCCESS: {result['message']}")
        else:
            print(f"   ❌ FAILED: Missing required fields or unsuccessful test")
            all_passed = False
    
    # Test multiple nodes with different statuses
    print(f"\n🧪 Test Scenario 4: Multiple nodes with different statuses")
    test_data = {"node_ids": [11, 1, 2337]}  # not_tested, ping_failed, ping_ok
    response = requests.post(f"{api_url}/manual/ping-test", json=test_data, headers=headers)
    
    if response.status_code != 200:
        print(f"   ❌ FAILED: API call failed with status {response.status_code}: {response.text}")
        all_passed = False
    else:
        result_data = response.json()
        
        if 'results' in result_data and len(result_data['results']) == 3:
            all_nodes_accepted = True
            for result in result_data['results']:
                if not result.get('success') or 'original_status' not in result:
                    all_nodes_accepted = False
                    break
                print(f"   Node {result.get('node_id')}: {result.get('message', 'No message')}")
            
            if all_nodes_accepted:
                print(f"   ✅ SUCCESS: All 3 nodes accepted regardless of status")
            else:
                print(f"   ❌ FAILED: Not all nodes were accepted properly")
                all_passed = False
        else:
            print(f"   ❌ FAILED: Expected 3 results, got: {len(result_data.get('results', []))}")
            all_passed = False
    
    # Final result
    print(f"\n📊 FINAL RESULT:")
    if all_passed:
        print(f"🎉 CRITICAL TEST PASSED: Ping test status restriction successfully removed!")
        print(f"✅ All nodes accepted regardless of current status")
        print(f"✅ Original status tracking working correctly")
        print(f"✅ Status transition messages showing correctly")
        return True
    else:
        print(f"❌ CRITICAL TEST FAILED: Some scenarios did not pass")
        return False

if __name__ == "__main__":
    success = test_ping_restriction_removal()
    exit(0 if success else 1)