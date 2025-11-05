#!/usr/bin/env python3

import requests
import json
from datetime import datetime
import time

# Debug timestamp issues
BASE_URL = "https://memory-mcp.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

def login():
    """Login and get token"""
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def debug_manual_ping():
    """Debug manual ping timestamp issue"""
    token = login()
    if not token:
        print("❌ Login failed")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("🔍 DEBUGGING MANUAL PING TIMESTAMP ISSUE")
    print("=" * 50)
    
    # Create a fresh node
    timestamp = str(int(time.time()))
    node_data = {
        "ip": f"192.168.250.{timestamp[-2:]}",
        "login": f"debugtest{timestamp[-4:]}",
        "password": "debugpass123",
        "protocol": "pptp"
    }
    
    print("1. Creating fresh node...")
    response = requests.post(f"{API_URL}/nodes", json=node_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to create node: {response.status_code}")
        return
    
    node = response.json()
    node_id = node['id']
    initial_timestamp = node.get('last_update')
    initial_status = node.get('status')
    
    print(f"   Node ID: {node_id}")
    print(f"   Initial Status: {initial_status}")
    print(f"   Initial Timestamp: {initial_timestamp}")
    
    # Wait a moment
    print("\n2. Waiting 3 seconds...")
    time.sleep(3)
    
    # Check node before ping test
    print("\n3. Checking node before ping test...")
    response = requests.get(f"{API_URL}/nodes?id={node_id}", headers=headers)
    if response.status_code == 200:
        nodes = response.json()['nodes']
        if nodes:
            node_before = nodes[0]
            print(f"   Status before ping: {node_before.get('status')}")
            print(f"   Timestamp before ping: {node_before.get('last_update')}")
    
    # Perform manual ping test
    print("\n4. Performing manual ping test...")
    ping_data = {"node_ids": [node_id]}
    response = requests.post(f"{API_URL}/manual/ping-test", json=ping_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Ping test response: {json.dumps(result, indent=2)}")
        
        # Check node after ping test
        print("\n5. Checking node after ping test...")
        response = requests.get(f"{API_URL}/nodes?id={node_id}", headers=headers)
        if response.status_code == 200:
            nodes = response.json()['nodes']
            if nodes:
                node_after = nodes[0]
                final_status = node_after.get('status')
                final_timestamp = node_after.get('last_update')
                
                print(f"   Status after ping: {final_status}")
                print(f"   Timestamp after ping: {final_timestamp}")
                
                # Compare timestamps
                if final_timestamp != initial_timestamp:
                    print(f"   ✅ TIMESTAMP CHANGED: {initial_timestamp} → {final_timestamp}")
                    
                    # Check if new timestamp is recent
                    try:
                        final_dt = datetime.fromisoformat(final_timestamp.replace('Z', '+00:00'))
                        now = datetime.now()
                        age = abs((now - final_dt).total_seconds())
                        
                        if age <= 60:
                            print(f"   ✅ NEW TIMESTAMP IS RECENT: {age:.1f}s ago")
                        else:
                            print(f"   ❌ NEW TIMESTAMP IS OLD: {age:.1f}s ago")
                    except Exception as e:
                        print(f"   ❌ TIMESTAMP PARSE ERROR: {e}")
                else:
                    print(f"   ❌ TIMESTAMP NOT CHANGED: Still {initial_timestamp}")
                
                # Check status change
                if final_status != initial_status:
                    print(f"   ✅ STATUS CHANGED: {initial_status} → {final_status}")
                else:
                    print(f"   ❌ STATUS NOT CHANGED: Still {initial_status}")
            else:
                print("   ❌ Node not found after ping test")
        else:
            print(f"   ❌ Failed to get node after ping: {response.status_code}")
    else:
        print(f"   ❌ Manual ping test failed: {response.status_code} - {response.text}")

def test_simple_import():
    """Test simple import with correct format"""
    token = login()
    if not token:
        print("❌ Login failed")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("\n🔍 DEBUGGING IMPORT ISSUE")
    print("=" * 30)
    
    # Test with a simple, valid IP
    timestamp = str(int(time.time()))
    import_data = {
        "data": f"""Ip: 192.168.1.{timestamp[-2:]}
Login: testuser{timestamp[-4:]}
Pass: testpass
State: California
City: Los Angeles""",
        "protocol": "pptp",
        "testing_mode": "no_test"
    }
    
    print(f"Import data: {import_data['data']}")
    
    response = requests.post(f"{API_URL}/nodes/import", json=import_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Import result: {json.dumps(result, indent=2)}")
        
        if result.get('report', {}).get('added', 0) > 0:
            print("✅ Import successful")
            
            # Get the imported node
            ip = f"192.168.1.{timestamp[-2:]}"
            response = requests.get(f"{API_URL}/nodes?ip={ip}", headers=headers)
            if response.status_code == 200:
                nodes = response.json()['nodes']
                if nodes:
                    node = nodes[0]
                    print(f"Imported node: IP={node.get('ip')}, Status={node.get('status')}, Timestamp={node.get('last_update')}")
                else:
                    print("❌ Imported node not found")
        else:
            print("❌ No nodes imported")
    else:
        print(f"❌ Import failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_manual_ping()
    test_simple_import()