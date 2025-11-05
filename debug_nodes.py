#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class DebugTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def make_request(self, method: str, endpoint: str, data=None, expected_status: int = 200):
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}

            return success, response_data

        except Exception as e:
            return False, {"error": str(e)}

    def login(self):
        """Login with admin credentials"""
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        else:
            print(f"❌ Login failed: {response}")
            return False

    def debug_nodes(self):
        """Debug what nodes were actually created"""
        print("🔍 Debugging created nodes...")
        
        # Get all nodes
        success, response = self.make_request('GET', 'nodes?limit=100')
        if success and 'nodes' in response:
            nodes = response['nodes']
            print(f"📊 Found {len(nodes)} nodes:")
            
            expected_ips = [
                '71.84.237.32', '144.229.29.35', '76.178.64.46', '96.234.52.227',
                '68.227.241.4', '96.42.187.97', '70.171.218.52', '24.227.222.13',
                '71.202.136.233', '24.227.222.112'
            ]
            
            found_ips = []
            for i, node in enumerate(nodes, 1):
                ip = node.get('ip', 'N/A')
                login = node.get('login', 'N/A')
                password = node.get('password', 'N/A')
                state = node.get('state', 'N/A')
                city = node.get('city', 'N/A')
                zipcode = node.get('zipcode', 'N/A')
                
                found_ips.append(ip)
                print(f"   {i}. IP: {ip}, Login: {login}, Pass: {password}, State: {state}, City: {city}, ZIP: {zipcode}")
            
            print(f"\n🎯 Expected IPs: {expected_ips}")
            print(f"🔍 Found IPs: {found_ips}")
            
            missing_ips = [ip for ip in expected_ips if ip not in found_ips]
            extra_ips = [ip for ip in found_ips if ip not in expected_ips]
            
            if missing_ips:
                print(f"❌ Missing IPs: {missing_ips}")
            if extra_ips:
                print(f"⚠️ Extra IPs: {extra_ips}")
            
            return nodes
        else:
            print(f"❌ Failed to get nodes: {response}")
            return []

def main():
    tester = DebugTester()
    if tester.login():
        tester.debug_nodes()

if __name__ == "__main__":
    main()