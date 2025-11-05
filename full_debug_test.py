#!/usr/bin/env python3

import requests
import sys

class FullDebugTester:
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
            if method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data)
            elif method == 'GET':
                response = requests.get(url, headers=headers, params=data)
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

    def clear_nodes(self):
        """Clear all nodes"""
        success, response = self.make_request('GET', 'nodes?limit=1000')
        if success and 'nodes' in response:
            nodes = response['nodes']
            if nodes:
                node_ids = [node['id'] for node in nodes]
                delete_data = {"node_ids": node_ids}
                self.make_request('DELETE', 'nodes', delete_data)
                print(f"🗑️ Cleared {len(node_ids)} nodes")

    def test_full_data_with_debug(self):
        """Test full user data with detailed debugging"""
        print("🔍 Testing full user data with detailed debugging...")
        
        self.clear_nodes()
        
        # Full user data
        user_data = """StealUrVPN
@StealUrVPN_bot

Ip: 71.84.237.32	a_reg_107
Login: admin
Pass: admin
State: California
City: Pasadena
Zip: 91101

Ip: 144.229.29.35
Login: admin
Pass: admin
State: California
City: Los Angeles
Zip: 90035
---------------------
GVBot
@gv2you_bot

76.178.64.46  admin admin CA
96.234.52.227  admin admin NJ
---------------------
Worldwide VPN Hub
@pptpmaster_bot

68.227.241.4 - admin:admin - Arizona/Phoenix 85001 | 2025-09-03 16:05:25
96.42.187.97 - 1:1 - Michigan/Lapeer 48446 | 2025-09-03 09:50:22

---------------------

PPTP INFINITY
@pptpinfinity_bot
70.171.218.52:admin:admin:US:Arizona:85001

> PPTP_SVOIM_VPN:
🚨 PPTP Connection
IP: 24.227.222.13
Credentials: admin:admin
Location: Texas (Austin)
ZIP: 78701

> PPTP_SVOIM_VPN:
🚨 PPTP Connection
IP: 71.202.136.233
Credentials: admin:admin
Location: California (Fremont)
ZIP: 94536

> PPTP_SVOIM_VPN:
🚨 PPTP Connection
IP: 24.227.222.112
Credentials: admin:admin
Location: Texas (Austin)
ZIP: 78701"""

        import_data = {
            "data": user_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            print(f"📊 Import Results:")
            print(f"   Total Processed: {report.get('total_processed', 0)}")
            print(f"   Successfully Parsed: {report.get('successfully_parsed', 0)}")
            print(f"   Added: {report.get('added', 0)}")
            print(f"   Skipped Duplicates: {report.get('skipped_duplicates', 0)}")
            print(f"   Format Errors: {report.get('format_errors', 0)}")
            
            # Show detailed results
            if 'details' in report:
                details = report['details']
                
                print(f"\n📝 Added Nodes:")
                for i, node in enumerate(details.get('added', []), 1):
                    print(f"   {i}. IP: {node.get('ip', 'N/A')}")
                
                print(f"\n⏭️ Skipped Nodes:")
                for i, node in enumerate(details.get('skipped', []), 1):
                    print(f"   {i}. IP: {node.get('ip', 'N/A')} (Reason: {node.get('reason', 'N/A')})")
                
                if details.get('format_errors'):
                    print(f"\n❌ Format Errors:")
                    for i, error in enumerate(details['format_errors'], 1):
                        print(f"   {i}. {error}")
            
            # Now check what nodes actually exist
            print(f"\n🔍 Checking actual nodes in database:")
            nodes_success, nodes_response = self.make_request('GET', 'nodes?limit=100')
            if nodes_success and 'nodes' in nodes_response:
                nodes = nodes_response['nodes']
                print(f"   Found {len(nodes)} nodes in database:")
                for i, node in enumerate(nodes, 1):
                    print(f"   {i}. IP: {node.get('ip', 'N/A')}, Login: {node.get('login', 'N/A')}, State: {node.get('state', 'N/A')}")
                
                # Check specifically for the missing IP
                missing_ip = '70.171.218.52'
                found_missing = any(node.get('ip') == missing_ip for node in nodes)
                print(f"\n🎯 Missing IP {missing_ip} found in database: {'✅ YES' if found_missing else '❌ NO'}")
                
                if not found_missing:
                    print(f"🔍 Searching for any nodes with similar IP pattern...")
                    similar_nodes = [node for node in nodes if '70.171' in node.get('ip', '')]
                    if similar_nodes:
                        for node in similar_nodes:
                            print(f"   Similar: {node.get('ip', 'N/A')}")
                    else:
                        print(f"   No similar IPs found")

def main():
    tester = FullDebugTester()
    if tester.login():
        tester.test_full_data_with_debug()

if __name__ == "__main__":
    main()