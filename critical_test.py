#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class CriticalTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

    def make_request(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> tuple:
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

    def clear_existing_nodes(self):
        """Clear existing nodes to avoid duplicates"""
        print("🧹 Clearing existing nodes to avoid duplicates...")
        
        # Get all nodes
        success, response = self.make_request('GET', 'nodes?limit=1000')
        if success and 'nodes' in response:
            nodes = response['nodes']
            if nodes:
                node_ids = [node['id'] for node in nodes]
                
                # Delete all nodes in batches
                batch_size = 50
                for i in range(0, len(node_ids), batch_size):
                    batch = node_ids[i:i+batch_size]
                    delete_data = {"node_ids": batch}
                    self.make_request('DELETE', 'nodes', delete_data)
                
                print(f"🗑️ Cleared {len(node_ids)} existing nodes")
            else:
                print("📝 No existing nodes to clear")
        else:
            print("⚠️ Could not retrieve nodes for clearing")

    def test_critical_real_user_data(self):
        """CRITICAL TEST - Real User Data with Multiple Configs (Review Request)"""
        print("\n🚨 CRITICAL TEST - Real User Data with Multiple Configs")
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
        
        print("📤 Sending import request with real user data...")
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            total_added = report.get('added', 0)
            total_processed = report.get('total_processed', 0)
            successfully_parsed = report.get('successfully_parsed', 0)
            format_errors = report.get('format_errors', 0)
            
            print(f"📊 Import Results:")
            print(f"   Total Processed: {total_processed}")
            print(f"   Successfully Parsed: {successfully_parsed}")
            print(f"   Added: {total_added}")
            print(f"   Format Errors: {format_errors}")
            print(f"   Skipped Duplicates: {report.get('skipped_duplicates', 0)}")
            
            # Expected: 10 nodes total
            if total_added >= 10:
                print(f"✅ SUCCESS: {total_added} nodes created (expected 10)")
                
                # Verify specific nodes were created correctly
                expected_nodes = [
                    {'ip': '71.84.237.32', 'login': 'admin', 'password': 'admin', 'state': 'California', 'city': 'Pasadena', 'zipcode': '91101'},
                    {'ip': '144.229.29.35', 'login': 'admin', 'password': 'admin', 'state': 'California', 'city': 'Los Angeles', 'zipcode': '90035'},
                    {'ip': '76.178.64.46', 'login': 'admin', 'password': 'admin', 'state': 'California'},
                    {'ip': '96.234.52.227', 'login': 'admin', 'password': 'admin', 'state': 'New Jersey'},
                    {'ip': '68.227.241.4', 'login': 'admin', 'password': 'admin', 'state': 'Arizona', 'city': 'Phoenix', 'zipcode': '85001'},
                    {'ip': '96.42.187.97', 'login': '1', 'password': '1', 'state': 'Michigan', 'city': 'Lapeer', 'zipcode': '48446'},
                    {'ip': '70.171.218.52', 'login': 'admin', 'password': 'admin', 'state': 'Arizona', 'zipcode': '85001'},
                    {'ip': '24.227.222.13', 'login': 'admin', 'password': 'admin', 'state': 'Texas', 'city': 'Austin', 'zipcode': '78701'},
                    {'ip': '71.202.136.233', 'login': 'admin', 'password': 'admin', 'state': 'California', 'city': 'Fremont', 'zipcode': '94536'},
                    {'ip': '24.227.222.112', 'login': 'admin', 'password': 'admin', 'state': 'Texas', 'city': 'Austin', 'zipcode': '78701'}
                ]
                
                print(f"\n🔍 Verifying individual nodes...")
                verified_count = 0
                
                for i, expected in enumerate(expected_nodes, 1):
                    # Check if this specific node was created
                    nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={expected["ip"]}')
                    
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        
                        # Verify all expected fields
                        node_correct = True
                        field_issues = []
                        
                        for key, expected_value in expected.items():
                            actual_value = node.get(key)
                            if actual_value != expected_value:
                                node_correct = False
                                field_issues.append(f"{key}: expected '{expected_value}', got '{actual_value}'")
                        
                        if node_correct:
                            verified_count += 1
                            print(f"   ✅ Node {i}: {expected['ip']} - {expected['login']}/{expected['password']} - {expected.get('state', 'N/A')}")
                        else:
                            print(f"   ❌ Node {i}: {expected['ip']} - Field issues: {', '.join(field_issues)}")
                    else:
                        print(f"   ❌ Node {i}: {expected['ip']} - Node not found")
                
                print(f"\n📈 VERIFICATION RESULTS: {verified_count}/10 nodes verified correctly")
                
                if verified_count >= 10:
                    print("🎉 CRITICAL TEST PASSED!")
                    print("✅ Headers ignored: StealUrVPN, GVBot, Worldwide VPN Hub, PPTP INFINITY")
                    print("✅ @mentions ignored: @StealUrVPN_bot, @gv2you_bot, @pptpmaster_bot, @pptpinfinity_bot")
                    print("✅ Multiple Format 1 configs split correctly (2 configs with Ip: in first block)")
                    print("✅ Multiple Format 6 configs split correctly (3 PPTP connections)")
                    print("✅ Extra text removed from IP: '71.84.237.32\\ta_reg_107' → '71.84.237.32'")
                    print("✅ State normalization: CA→California, NJ→New Jersey")
                    print("✅ All formats detected and parsed")
                    return True
                else:
                    print("❌ CRITICAL TEST FAILED!")
                    print(f"❌ Only {verified_count}/10 nodes verified correctly")
                    return False
            else:
                print(f"❌ CRITICAL TEST FAILED!")
                print(f"❌ Only {total_added} nodes created, expected 10")
                print(f"❌ Smart parser failed to handle mixed formats correctly")
                
                # Show detailed report for debugging
                if 'details' in report:
                    details = report['details']
                    print(f"\n🔍 DEBUG INFO:")
                    print(f"   Added nodes: {len(details.get('added', []))}")
                    print(f"   Skipped duplicates: {len(details.get('skipped', []))}")
                    print(f"   Format errors: {len(details.get('format_errors', []))}")
                    
                    if details.get('format_errors'):
                        print(f"   Format error details:")
                        for error in details['format_errors'][:5]:  # Show first 5 errors
                            print(f"     - {error}")
                
                return False
        else:
            print(f"❌ CRITICAL TEST FAILED!")
            print(f"❌ Failed to import real user data: {response}")
            return False

    def run_critical_test(self):
        """Run the critical test"""
        print("🚀 Starting Critical Test - Real User Data with Multiple Configs")
        print("=" * 70)
        
        # Login first
        if not self.login():
            return False
        
        # Clear existing nodes to avoid duplicates
        self.clear_existing_nodes()
        
        # Run the critical test
        result = self.test_critical_real_user_data()
        
        print("\n" + "=" * 70)
        if result:
            print("🎉 CRITICAL TEST RESULT: PASSED")
            print("✅ Smart parser correctly handles real user data with multiple formats")
        else:
            print("❌ CRITICAL TEST RESULT: FAILED")
            print("❌ Smart parser has issues with real user data")
        
        return result

def main():
    tester = CriticalTester()
    success = tester.run_critical_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())