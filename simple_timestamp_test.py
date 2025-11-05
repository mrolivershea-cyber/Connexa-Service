#!/usr/bin/env python3

import requests
import json
from datetime import datetime
import time

def test_timestamp_update():
    base_url = "https://memory-mcp.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Create a test node
    test_node = {
        "ip": "192.168.99.99",
        "login": "timestamptest",
        "password": "testpass123",
        "protocol": "pptp",
        "status": "not_tested"
    }
    
    response = requests.post(f"{api_url}/nodes", json=test_node, headers=headers)
    if response.status_code != 200:
        print(f"❌ Node creation failed: {response.text}")
        return
    
    node_data = response.json()
    node_id = node_data['id']
    initial_timestamp = node_data.get('last_update')
    
    print(f"✅ Created node {node_id} with initial timestamp: {initial_timestamp}")
    
    # Wait a moment
    time.sleep(2)
    
    print(f"Current Python time before ping test: {datetime.utcnow().isoformat()}")
    
    # Try manual ping test
    ping_data = {"node_ids": [node_id]}
    response = requests.post(f"{api_url}/manual/ping-test", json=ping_data, headers=headers)
    
    print(f"Manual ping test response: {response.status_code}")
    print(f"Response body: {response.text}")
    
    print(f"Current Python time after ping test: {datetime.utcnow().isoformat()}")
    
    # Check node status after ping test via API
    response = requests.get(f"{api_url}/nodes?id={node_id}", headers=headers)
    if response.status_code == 200:
        nodes = response.json()['nodes']
        if nodes:
            node = nodes[0]
            new_timestamp = node.get('last_update')
            new_status = node.get('status')
            
            print(f"After ping test (via API):")
            print(f"  Status: {new_status}")
            print(f"  Timestamp: {new_timestamp}")
            print(f"  Timestamp changed: {new_timestamp != initial_timestamp}")
            
            # Parse timestamps to compare
            try:
                initial_dt = datetime.fromisoformat(initial_timestamp.replace('Z', '+00:00'))
                new_dt = datetime.fromisoformat(new_timestamp.replace('Z', '+00:00'))
                time_diff = (new_dt - initial_dt).total_seconds()
                print(f"  Time difference: {time_diff:.2f} seconds")
                
                if time_diff > 0:
                    print("  ✅ Timestamp was updated to a newer time")
                elif time_diff < 0:
                    print("  ❌ Timestamp was updated to an OLDER time")
                else:
                    print("  ❌ Timestamp was not changed")
            except Exception as e:
                print(f"  Error parsing timestamps: {e}")
        else:
            print("❌ Node not found after ping test")
    else:
        print(f"❌ Failed to get node after ping test: {response.text}")
    
    # Also check database directly
    import sqlite3
    try:
        conn = sqlite3.connect('/app/backend/connexa.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, ip, status, last_update, created_at FROM nodes WHERE id = ?", (node_id,))
        db_node = cursor.fetchone()
        if db_node:
            print(f"After ping test (direct DB query):")
            print(f"  ID: {db_node[0]}, IP: {db_node[1]}, Status: {db_node[2]}")
            print(f"  Last Update: {db_node[3]}, Created: {db_node[4]}")
        else:
            print("❌ Node not found in database")
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")
    
    # Clean up - delete the test node
    requests.delete(f"{api_url}/nodes/{node_id}", headers=headers)
    print(f"✅ Cleaned up test node {node_id}")

if __name__ == "__main__":
    test_timestamp_update()