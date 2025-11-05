#!/usr/bin/env python3

import requests
import json

# Test alternative delete endpoints
base_url = "https://memory-mcp.preview.emergentagent.com"
api_url = f"{base_url}/api"

# Login
login_data = {"username": "admin", "password": "admin"}
response = requests.post(f"{api_url}/auth/login", json=login_data)
token = response.json()['access_token']
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}

print("🔍 TESTING ALTERNATIVE DELETE ENDPOINTS")
print("=" * 40)

# Get some existing node IDs
response1 = requests.get(f"{api_url}/nodes?limit=3", headers=headers)
if response1.status_code == 200:
    nodes = response1.json().get('nodes', [])
    if len(nodes) >= 2:
        node_id1 = nodes[0]['id']
        node_id2 = nodes[1]['id']
        
        print(f"Testing with node IDs: {node_id1}, {node_id2}")
        
        # Test 1: Regular /nodes DELETE endpoint (should work)
        delete_data = {
            "node_ids": [node_id1, node_id2]
        }
        
        response2 = requests.delete(f"{api_url}/nodes", json=delete_data, headers=headers)
        print(f"DELETE /nodes: {response2.status_code}")
        
        if response2.status_code == 200:
            result = response2.json()
            print(f"✅ Regular delete endpoint working: {result}")
        else:
            print(f"❌ Regular delete failed: {response2.text}")
            
        # Test 2: Individual node deletion
        if len(nodes) >= 3:
            node_id3 = nodes[2]['id']
            response3 = requests.delete(f"{api_url}/nodes/{node_id3}", headers=headers)
            print(f"DELETE /nodes/{node_id3}: {response3.status_code}")
            
            if response3.status_code == 200:
                result = response3.json()
                print(f"✅ Individual delete working: {result}")
            else:
                print(f"❌ Individual delete failed: {response3.text}")

print("\n" + "=" * 40)