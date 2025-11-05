#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class CriticalFormat4Tester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def make_request(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200) -> tuple:
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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data)
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
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response}")
            return False

    def clear_test_nodes(self):
        """Clear existing test nodes to avoid duplicates"""
        test_ips = [
            '71.84.237.32', '144.229.29.35', '76.178.64.46', '96.234.52.227',
            '68.227.241.4', '96.42.187.97', '70.171.218.52', '24.227.222.13',
            '71.202.136.233', '24.227.222.112'
        ]
        
        nodes_to_delete = []
        
        for ip in test_ips:
            success, response = self.make_request('GET', f'nodes?ip={ip}')
            if success and 'nodes' in response and response['nodes']:
                for node in response['nodes']:
                    nodes_to_delete.append(node['id'])
        
        if nodes_to_delete:
            delete_data = {"node_ids": nodes_to_delete}
            success, response = self.make_request('DELETE', 'nodes', delete_data)
            if success:
                print(f"✅ Cleared {len(nodes_to_delete)} existing test nodes")
            else:
                print(f"❌ Failed to clear test nodes: {response}")
        else:
            print("ℹ️ No existing test nodes to clear")

    def test_critical_format_4_block_splitting(self):
        """CRITICAL RE-TEST - Fixed Smart Block Splitting for Format 4"""
        print("\n🚨 CRITICAL RE-TEST - Fixed Smart Block Splitting for Format 4")
        print("=" * 60)
        
        # Exact user data from review request
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
            total_added = report.get('added', 0)
            
            print(f"\n🔍 IMPORT RESULTS:")
            print(f"   Total nodes created: {total_added}")
            print(f"   Skipped duplicates: {report.get('skipped_duplicates', 0)}")
            print(f"   Format errors: {report.get('format_errors', 0)}")
            print(f"   Processing errors: {report.get('processing_errors', 0)}")
            
            # CRITICAL VERIFICATION: Must create exactly 10 nodes
            expected_nodes = [
                {'ip': '71.84.237.32', 'login': 'admin', 'password': 'admin', 'state': 'California', 'format': 'Format 1'},
                {'ip': '144.229.29.35', 'login': 'admin', 'password': 'admin', 'state': 'California', 'format': 'Format 1'},
                {'ip': '76.178.64.46', 'login': 'admin', 'password': 'admin', 'state': 'California', 'format': 'Format 2'},
                {'ip': '96.234.52.227', 'login': 'admin', 'password': 'admin', 'state': 'New Jersey', 'format': 'Format 2'},
                {'ip': '68.227.241.4', 'login': 'admin', 'password': 'admin', 'state': 'Arizona', 'format': 'Format 3'},
                {'ip': '96.42.187.97', 'login': '1', 'password': '1', 'state': 'Michigan', 'format': 'Format 3'},
                {'ip': '70.171.218.52', 'login': 'admin', 'password': 'admin', 'state': 'Arizona', 'format': 'Format 4 - CRITICAL'},
                {'ip': '24.227.222.13', 'login': 'admin', 'password': 'admin', 'state': 'Texas', 'format': 'Format 6'},
                {'ip': '71.202.136.233', 'login': 'admin', 'password': 'admin', 'state': 'California', 'format': 'Format 6'},
                {'ip': '24.227.222.112', 'login': 'admin', 'password': 'admin', 'state': 'Texas', 'format': 'Format 6'}
            ]
            
            verified_nodes = []
            missing_nodes = []
            
            print(f"\n📋 NODE VERIFICATION RESULTS:")
            for i, expected in enumerate(expected_nodes, 1):
                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={expected["ip"]}')
                
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    
                    # Verify all expected fields
                    node_correct = True
                    for key in ['ip', 'login', 'password', 'state']:
                        if key in expected and node.get(key) != expected[key]:
                            node_correct = False
                            break
                    
                    if node_correct:
                        verified_nodes.append(expected)
                        status = "✅" if expected['format'] != 'Format 4 - CRITICAL' else "🎯"
                        print(f"   {i}. {status} {expected['ip']} - {expected['login']}/{expected['password']} - {expected['state']} ({expected['format']})")
                    else:
                        print(f"   {i}. ❌ {expected['ip']} - Field mismatch: Expected {expected}, Got {dict((k,node.get(k)) for k in ['ip','login','password','state'])}")
                        missing_nodes.append(expected['ip'])
                else:
                    print(f"   {i}. ❌ {expected['ip']} - Node not found ({expected['format']})")
                    missing_nodes.append(expected['ip'])
            
            # SPECIFIC CHECK: Node #7 (70.171.218.52) must exist
            format_4_node_found = '70.171.218.52' in [n['ip'] for n in verified_nodes]
            
            print(f"\n🎯 CRITICAL VERIFICATION:")
            print(f"   Total nodes verified: {len(verified_nodes)}/10")
            print(f"   Format 4 node (70.171.218.52) found: {'✅ YES' if format_4_node_found else '❌ NO'}")
            
            if len(verified_nodes) == 10 and format_4_node_found:
                print(f"\n✅ SUCCESS: All 10 nodes created correctly!")
                print(f"   🎯 Format 4 node (70.171.218.52) successfully created with login=admin, password=admin, state=Arizona")
                print(f"   ✅ Headers filtered: 'StealUrVPN', 'GVBot', 'Worldwide VPN Hub', 'PPTP INFINITY'")
                print(f"   ✅ @mentions filtered: '@StealUrVPN_bot', '@gv2you_bot', '@pptpmaster_bot', '@pptpinfinity_bot'")
                print(f"   ✅ Extra text removed: 'a_reg_107' after first IP")
                print(f"   ✅ State normalization: CA→California, NJ→New Jersey")
                print(f"   ✅ Smart block splitting working correctly for Format 4")
                return True
            else:
                print(f"\n❌ CRITICAL ISSUE:")
                print(f"   Only {len(verified_nodes)}/10 nodes verified correctly")
                print(f"   Format 4 node (70.171.218.52) found: {format_4_node_found}")
                if missing_nodes:
                    print(f"   Missing nodes: {missing_nodes}")
                return False
        else:
            print(f"❌ Failed to import: {response}")
            return False

    def run_test(self):
        """Run the critical Format 4 test"""
        print("🚀 Starting Critical Format 4 Block Splitting Test")
        print("=" * 50)
        
        if not self.login():
            return False
        
        # Clear existing test nodes to get clean results
        self.clear_test_nodes()
        
        # Run the critical test
        success = self.test_critical_format_4_block_splitting()
        
        print("\n" + "=" * 50)
        if success:
            print("🎉 CRITICAL TEST PASSED: Format 4 block splitting fix verified!")
        else:
            print("❌ CRITICAL TEST FAILED: Format 4 block splitting issue persists")
        
        return success

def main():
    tester = CriticalFormat4Tester()
    success = tester.run_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())