#!/usr/bin/env python3

import requests
import json

# Test node retrieval
base_url = "https://memory-mcp.preview.emergentagent.com"
api_url = f"{base_url}/api"

# Login
login_data = {"username": "admin", "password": "admin"}
response = requests.post(f"{api_url}/auth/login", json=login_data)
token = response.json()['access_token']
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}

print("🔍 TESTING NODE RETRIEVAL")
print("=" * 30)

# Create a test node
test_data = {
    "data": "10.0.252.1:retrievetest:retrievepass",
    "protocol": "pptp"
}

response1 = requests.post(f"{api_url}/nodes/import", json=test_data, headers=headers)
print(f"Test node created: {response1.status_code}")
print(f"Response: {response1.json()}")

# Try to retrieve it
response2 = requests.get(f"{api_url}/nodes?login=retrievetest", headers=headers)
print(f"Node retrieval: {response2.status_code}")
print(f"Response: {response2.json()}")

# Try to get all nodes (limited)
response3 = requests.get(f"{api_url}/nodes?limit=5", headers=headers)
print(f"All nodes (limited): {response3.status_code}")
if response3.status_code == 200:
    nodes = response3.json().get('nodes', [])
    print(f"Found {len(nodes)} nodes")
    for node in nodes[:3]:  # Show first 3
        print(f"  - ID: {node.get('id')}, IP: {node.get('ip')}, Login: {node.get('login')}")

print("\n" + "=" * 30)