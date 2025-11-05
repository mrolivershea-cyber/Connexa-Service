#!/usr/bin/env python3

import requests
import json
import time

class SOCKSDetailedTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def login(self):
        """Login with admin credentials"""
        login_data = {"username": "admin", "password": "admin"}
        response = requests.post(f"{self.api_url}/auth/login", json=login_data, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            self.headers['Authorization'] = f'Bearer {self.token}'
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False

    def get_nodes_by_status(self, status):
        """Get nodes by specific status"""
        response = requests.get(f"{self.api_url}/nodes?status={status}&limit=10", headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            return data['nodes']
        return []

    def test_socks_start_detailed(self, node_ids):
        """Test SOCKS start with detailed logging"""
        print(f"\n🔍 DETAILED SOCKS START TEST")
        print(f"Testing with node IDs: {node_ids}")
        
        # Get node details before start
        print("\n📋 Node details BEFORE SOCKS start:")
        for node_id in node_ids:
            response = requests.get(f"{self.api_url}/nodes/{node_id}", headers=self.headers)
            if response.status_code == 200:
                node = response.json()
                print(f"   Node {node_id}: {node['ip']} - Status: {node['status']} - SOCKS Port: {node.get('socks_port', 'None')}")
        
        # Start SOCKS
        start_data = {"node_ids": node_ids}
        print(f"\n🚀 Starting SOCKS for nodes: {node_ids}")
        response = requests.post(f"{self.api_url}/socks/start", json=start_data, headers=self.headers)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SOCKS Start Response: {json.dumps(result, indent=2)}")
            
            # Wait a moment for services to start
            time.sleep(2)
            
            # Get node details after start
            print("\n📋 Node details AFTER SOCKS start:")
            for node_id in node_ids:
                response = requests.get(f"{self.api_url}/nodes/{node_id}", headers=self.headers)
                if response.status_code == 200:
                    node = response.json()
                    print(f"   Node {node_id}: {node['ip']} - Status: {node['status']} - SOCKS Port: {node.get('socks_port', 'None')}")
            
            # Check active proxies
            print("\n🔍 Active SOCKS proxies:")
            response = requests.get(f"{self.api_url}/socks/active", headers=self.headers)
            if response.status_code == 200:
                proxies = response.json()
                print(f"Active proxies count: {len(proxies.get('proxies', []))}")
                for proxy in proxies.get('proxies', []):
                    print(f"   - {proxy}")
            
            # Check proxy file
            print("\n📄 Proxy file content:")
            response = requests.get(f"{self.api_url}/socks/proxy-file", headers=self.headers)
            if response.status_code == 200:
                file_data = response.json()
                content = file_data.get('content', '')
                lines = content.split('\n')
                active_count = 0
                for line in lines:
                    if line.strip() and 'socks5://' in line:
                        active_count += 1
                        print(f"   Active proxy: {line.strip()}")
                print(f"Total active proxies in file: {active_count}")
            
            return result
        else:
            print(f"❌ SOCKS Start failed: {response.text}")
            return None

    def run_investigation(self):
        """Run the detailed SOCKS investigation"""
        print("🇷🇺 DETAILED SOCKS FUNCTIONALITY INVESTIGATION")
        print("=" * 80)
        
        if not self.login():
            return False
        
        # Get nodes with different statuses
        speed_ok_nodes = self.get_nodes_by_status('speed_ok')
        ping_ok_nodes = self.get_nodes_by_status('ping_ok')
        ping_failed_nodes = self.get_nodes_by_status('ping_failed')
        
        print(f"\n📊 Available nodes:")
        print(f"   speed_ok: {len(speed_ok_nodes)} nodes")
        print(f"   ping_ok: {len(ping_ok_nodes)} nodes")
        print(f"   ping_failed: {len(ping_failed_nodes)} nodes")
        
        # Test 1: Try with 6 speed_ok nodes (simulating user scenario)
        if len(speed_ok_nodes) >= 6:
            test_nodes = [n['id'] for n in speed_ok_nodes[:6]]
            print(f"\n🎯 TEST 1: Starting SOCKS with 6 speed_ok nodes")
            result = self.test_socks_start_detailed(test_nodes)
            
            if result:
                successful = result.get('successful', [])
                failed = result.get('failed', [])
                print(f"\n📊 RESULTS:")
                print(f"   Successful: {len(successful)} nodes")
                print(f"   Failed: {len(failed)} nodes")
                
                if len(successful) < 6:
                    print(f"\n❌ ISSUE IDENTIFIED: Only {len(successful)}/6 nodes started successfully")
                    print("Failed nodes:")
                    for fail in failed:
                        print(f"   - Node {fail.get('node_id')}: {fail.get('error', 'Unknown error')}")
        
        # Test 2: Try with mixed status nodes
        mixed_nodes = []
        if speed_ok_nodes:
            mixed_nodes.extend([n['id'] for n in speed_ok_nodes[:3]])
        if ping_ok_nodes:
            mixed_nodes.extend([n['id'] for n in ping_ok_nodes[:2]])
        if ping_failed_nodes:
            mixed_nodes.extend([n['id'] for n in ping_failed_nodes[:1]])
        
        if len(mixed_nodes) >= 3:
            print(f"\n🎯 TEST 2: Starting SOCKS with mixed status nodes")
            result = self.test_socks_start_detailed(mixed_nodes)

if __name__ == "__main__":
    tester = SOCKSDetailedTester()
    tester.run_investigation()