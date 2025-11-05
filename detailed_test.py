#!/usr/bin/env python3

import requests
import sys

class DetailedTester:
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

    def test_step_by_step(self):
        """Test step by step to isolate the issue"""
        print("🔍 Step-by-step testing to isolate the issue...")
        
        # Test 1: Just the Format 4 line
        print("\n1️⃣ Testing Format 4 line alone:")
        self.clear_nodes()
        test1 = "70.171.218.52:admin:admin:US:Arizona:85001"
        success1, response1 = self.make_request('POST', 'nodes/import', {"data": test1, "protocol": "pptp"})
        if success1:
            print(f"   Result: {response1['report']['added']} nodes added")
        
        # Test 2: Format 4 line with header above
        print("\n2️⃣ Testing Format 4 line with header:")
        self.clear_nodes()
        test2 = """PPTP INFINITY
70.171.218.52:admin:admin:US:Arizona:85001"""
        success2, response2 = self.make_request('POST', 'nodes/import', {"data": test2, "protocol": "pptp"})
        if success2:
            print(f"   Result: {response2['report']['added']} nodes added")
        
        # Test 3: Format 4 line with @mention above
        print("\n3️⃣ Testing Format 4 line with @mention:")
        self.clear_nodes()
        test3 = """@pptpinfinity_bot
70.171.218.52:admin:admin:US:Arizona:85001"""
        success3, response3 = self.make_request('POST', 'nodes/import', {"data": test3, "protocol": "pptp"})
        if success3:
            print(f"   Result: {response3['report']['added']} nodes added")
        
        # Test 4: Format 4 line with both header and @mention
        print("\n4️⃣ Testing Format 4 line with header and @mention:")
        self.clear_nodes()
        test4 = """PPTP INFINITY
@pptpinfinity_bot
70.171.218.52:admin:admin:US:Arizona:85001"""
        success4, response4 = self.make_request('POST', 'nodes/import', {"data": test4, "protocol": "pptp"})
        if success4:
            print(f"   Result: {response4['report']['added']} nodes added")
            if response4['report']['added'] == 0:
                print(f"   Debug: Processed: {response4['report']['total_processed']}, Parsed: {response4['report']['successfully_parsed']}")
                if 'details' in response4['report'] and 'format_errors' in response4['report']['details']:
                    for error in response4['report']['details']['format_errors']:
                        print(f"   Error: {error}")
        
        # Test 5: The exact section from user data
        print("\n5️⃣ Testing exact section from user data:")
        self.clear_nodes()
        test5 = """---------------------

PPTP INFINITY
@pptpinfinity_bot
70.171.218.52:admin:admin:US:Arizona:85001

> PPTP_SVOIM_VPN:"""
        success5, response5 = self.make_request('POST', 'nodes/import', {"data": test5, "protocol": "pptp"})
        if success5:
            print(f"   Result: {response5['report']['added']} nodes added")
            if response5['report']['added'] == 0:
                print(f"   Debug: Processed: {response5['report']['total_processed']}, Parsed: {response5['report']['successfully_parsed']}")

def main():
    tester = DetailedTester()
    if tester.login():
        tester.test_step_by_step()

if __name__ == "__main__":
    main()