#!/usr/bin/env python3

import requests
import json

# Test the batch delete functionality
base_url = "https://memory-mcp.preview.emergentagent.com"
api_url = f"{base_url}/api"

# Login
login_data = {"username": "admin", "password": "admin"}
response = requests.post(f"{api_url}/auth/login", json=login_data)
token = response.json()['access_token']
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}

print("🇷🇺 TESTING BATCH DELETE FUNCTIONALITY")
print("=" * 50)

# Create test nodes
test_data = {
    "data": "10.0.251.1:batchtest1:batchpass1\n10.0.251.2:batchtest2:batchpass2",
    "protocol": "pptp"
}

response1 = requests.post(f"{api_url}/nodes/import", json=test_data, headers=headers)
print(f"Test nodes created: {response1.status_code}")

if response1.status_code == 200:
    # Get the node IDs
    nodes_response1 = requests.get(f"{api_url}/nodes?login=batchtest1", headers=headers)
    nodes_response2 = requests.get(f"{api_url}/nodes?login=batchtest2", headers=headers)
    
    if nodes_response1.status_code == 200 and nodes_response2.status_code == 200:
        nodes1 = nodes_response1.json().get('nodes', [])
        nodes2 = nodes_response2.json().get('nodes', [])
        
        if nodes1 and nodes2:
            node_id1 = nodes1[0]['id']
            node_id2 = nodes2[0]['id']
            
            print(f"Found node IDs: {node_id1}, {node_id2}")
            
            # Test batch delete
            batch_delete_data = {
                "node_ids": [node_id1, node_id2]
            }
            
            response2 = requests.delete(f"{api_url}/nodes/batch", json=batch_delete_data, headers=headers)
            print(f"Batch delete: {response2.status_code}")
            
            if response2.status_code == 200:
                result = response2.json()
                deleted_count = result.get('deleted_count', 0)
                print(f"✅ Batch delete working: {deleted_count} nodes deleted")
            else:
                print(f"❌ Batch delete failed: {response2.text}")
        else:
            print("❌ Could not find created nodes")
    else:
        print("❌ Could not retrieve node IDs")

print("\n" + "=" * 50)
print("🏁 BATCH DELETE TEST COMPLETE")