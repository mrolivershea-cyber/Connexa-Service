#!/usr/bin/env python3

import requests
import sys

class DatabaseInspector:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def login(self):
        """Login and get token"""
        login_data = {"username": "admin", "password": "admin"}
        response = requests.post(f"{self.api_url}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.headers['Authorization'] = f'Bearer {self.token}'
            return True
        return False

    def inspect_ip(self, ip):
        """Inspect all nodes with a specific IP"""
        response = requests.get(f"{self.api_url}/nodes", 
                              headers=self.headers, 
                              params={'ip': ip, 'limit': 100})
        
        if response.status_code == 200:
            data = response.json()
            nodes = data.get('nodes', [])
            
            print(f"\n🔍 INSPECTING IP: {ip}")
            print(f"   Found {len(nodes)} nodes")
            
            # Group by credentials
            cred_groups = {}
            for node in nodes:
                key = f"{node.get('login', 'N/A')}:{node.get('password', 'N/A')}"
                if key not in cred_groups:
                    cred_groups[key] = []
                cred_groups[key].append(node)
            
            print(f"   Credential groups: {len(cred_groups)}")
            
            for creds, group_nodes in cred_groups.items():
                print(f"   - {creds}: {len(group_nodes)} nodes")
                if len(group_nodes) > 1:
                    print(f"     ⚠️  DUPLICATE CREDENTIALS FOUND!")
                    for node in group_nodes[:3]:  # Show first 3
                        print(f"       ID: {node.get('id')}, State: {node.get('state')}, Last Update: {node.get('last_update')}")
            
            return len(nodes), cred_groups
        else:
            print(f"❌ Failed to get nodes for {ip}: {response.text}")
            return 0, {}

    def run_inspection(self):
        """Run database inspection"""
        if not self.login():
            print("❌ Login failed")
            return False
        
        # Check the problematic IPs
        problem_ips = ['24.227.222.2', '98.127.101.184', '71.65.133.123']
        
        for ip in problem_ips:
            count, groups = self.inspect_ip(ip)
            
            if count > 1:
                print(f"🚨 PROBLEM: {ip} has {count} instances (should be 1)")
            else:
                print(f"✅ OK: {ip} has {count} instance(s)")

if __name__ == "__main__":
    inspector = DatabaseInspector()
    inspector.run_inspection()