#!/usr/bin/env python3

import requests
import json

def check_nodes():
    base_url = "https://memory-mcp.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Get stats
    stats_response = requests.get(f"{api_url}/stats", headers=headers)
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"📊 Database Stats:")
        print(f"   Total: {stats.get('total', 0)}")
        print(f"   Not tested: {stats.get('not_tested', 0)}")
        print(f"   Ping failed: {stats.get('ping_failed', 0)}")
        print(f"   Ping OK: {stats.get('ping_ok', 0)}")
    
    # Check specific nodes mentioned in review request
    node_ids = [6, 1, 2337]
    
    for node_id in node_ids:
        response = requests.get(f"{api_url}/nodes?page=1&limit=1000", headers=headers)
        if response.status_code == 200:
            nodes = response.json()['nodes']
            node = next((n for n in nodes if n['id'] == node_id), None)
            if node:
                print(f"Node {node_id}: IP={node['ip']}, Status={node['status']}")
            else:
                print(f"Node {node_id}: NOT FOUND")
    
    # Get some nodes with different statuses
    print(f"\n📋 Sample nodes by status:")
    
    # Get not_tested nodes
    response = requests.get(f"{api_url}/nodes?status=not_tested&limit=3", headers=headers)
    if response.status_code == 200:
        nodes = response.json()['nodes']
        print(f"Not tested nodes:")
        for node in nodes[:3]:
            print(f"   ID {node['id']}: {node['ip']} - {node['status']}")
    
    # Get ping_failed nodes
    response = requests.get(f"{api_url}/nodes?status=ping_failed&limit=3", headers=headers)
    if response.status_code == 200:
        nodes = response.json()['nodes']
        print(f"Ping failed nodes:")
        for node in nodes[:3]:
            print(f"   ID {node['id']}: {node['ip']} - {node['status']}")
    
    # Get ping_ok nodes
    response = requests.get(f"{api_url}/nodes?status=ping_ok&limit=3", headers=headers)
    if response.status_code == 200:
        nodes = response.json()['nodes']
        print(f"Ping OK nodes:")
        for node in nodes[:3]:
            print(f"   ID {node['id']}: {node['ip']} - {node['status']}")

if __name__ == "__main__":
    check_nodes()