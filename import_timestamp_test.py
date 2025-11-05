#!/usr/bin/env python3

import requests
import json
from datetime import datetime
import time

# Test import with correct format
BASE_URL = "https://memory-mcp.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

def login():
    """Login and get token"""
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def test_import_timestamp():
    """Test import with correct format"""
    token = login()
    if not token:
        print("❌ Login failed")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("🕒 TESTING IMPORT TIMESTAMP FIX")
    print("=" * 40)
    
    # Test with correct format: testuser:testpass@10.10.10.10:1723
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
    
    before_import = datetime.now()
    response = requests.post(f"{API_URL}/nodes/import", json=import_data, headers=headers)
    after_import = datetime.now()
    
    if response.status_code == 200:
        result = response.json()
        print(f"Import response: {result}")
        
        if result.get('report', {}).get('added', 0) > 0:
            print(f"✅ Import successful: {result['report']['added']} nodes added")
            
            # Get the imported node
            ip = f"10.10.10.{timestamp[-2:]}"
            response = requests.get(f"{API_URL}/nodes?ip={ip}", headers=headers)
            if response.status_code == 200:
                nodes = response.json()['nodes']
                if nodes:
                    node = nodes[0]
                    last_update_str = node.get('last_update')
                    status = node.get('status')
                    print(f"Node details: IP={node.get('ip')}, Status={status}, Timestamp={last_update_str}")
                    
                    if last_update_str:
                        try:
                            last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                            time_diff = abs((after_import - last_update).total_seconds())
                            
                            if time_diff <= 120:  # Within 2 minutes
                                print(f"✅ IMPORT TIMESTAMP CORRECT: {last_update_str} (diff: {time_diff:.1f}s)")
                                
                                # Verify status is 'not_tested' as expected
                                if status == 'not_tested':
                                    print(f"✅ IMPORT STATUS CORRECT: {status}")
                                else:
                                    print(f"❌ IMPORT STATUS INCORRECT: {status} (expected: not_tested)")
                                
                                return True
                            else:
                                print(f"❌ IMPORT TIMESTAMP TOO OLD: {last_update_str} (diff: {time_diff:.1f}s)")
                                return False
                        except Exception as e:
                            print(f"❌ TIMESTAMP PARSE ERROR: {e}")
                            return False
                    else:
                        print("❌ NO TIMESTAMP IN RESPONSE")
                        return False
                else:
                    print("❌ IMPORTED NODE NOT FOUND")
                    return False
            else:
                print(f"❌ Failed to get imported node: {response.status_code}")
                return False
        else:
            print(f"❌ No nodes added: {result}")
            return False
    else:
        print(f"❌ Import failed: {response.status_code} - {response.text}")
        return False

def test_manual_ping_on_fresh_node():
    """Test manual ping on a freshly created node"""
    token = login()
    if not token:
        print("❌ Login failed")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\n🔧 TESTING MANUAL PING TIMESTAMP UPDATE")
    print("=" * 40)
    
    # Create a fresh node
    timestamp = str(int(time.time()))
    node_data = {
        "ip": f"192.168.100.{timestamp[-2:]}",
        "login": f"pingtest{timestamp[-4:]}",
        "password": "pingpass123",
        "protocol": "pptp"
    }
    
    response = requests.post(f"{API_URL}/nodes", json=node_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create test node: {response.status_code}")
        return False
    
    node = response.json()
    node_id = node['id']
    initial_timestamp = node.get('last_update')
    print(f"Created node {node_id} with initial timestamp: {initial_timestamp}")
    
    # Wait a moment
    time.sleep(2)
    
    # Perform manual ping test
    ping_data = {"node_ids": [node_id]}
    response = requests.post(f"{API_URL}/manual/ping-test", json=ping_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Ping test result: {result}")
        
        # Get updated node
        response = requests.get(f"{API_URL}/nodes?id={node_id}", headers=headers)
        if response.status_code == 200:
            nodes = response.json()['nodes']
            if nodes:
                updated_node = nodes[0]
                new_timestamp = updated_node.get('last_update')
                new_status = updated_node.get('status')
                
                print(f"After ping: Status={new_status}, Timestamp={new_timestamp}")
                
                if new_timestamp != initial_timestamp:
                    print(f"✅ PING TEST TIMESTAMP UPDATED: {initial_timestamp} → {new_timestamp}")
                    return True
                else:
                    print(f"❌ PING TEST TIMESTAMP NOT UPDATED: Still {initial_timestamp}")
                    return False
            else:
                print("❌ Updated node not found")
                return False
        else:
            print(f"❌ Failed to get updated node: {response.status_code}")
            return False
    else:
        print(f"❌ Manual ping test failed: {response.status_code} - {response.text}")
        return False

if __name__ == "__main__":
    import_success = test_import_timestamp()
    ping_success = test_manual_ping_on_fresh_node()
    
    print("\n" + "=" * 50)
    print("TIMESTAMP FIX TEST SUMMARY:")
    print(f"Import timestamp: {'✅ PASSED' if import_success else '❌ FAILED'}")
    print(f"Manual ping timestamp: {'✅ PASSED' if ping_success else '❌ FAILED'}")
    print("=" * 50)