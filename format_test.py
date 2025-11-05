#!/usr/bin/env python3

import requests
import sys

class FormatTester:
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

    def test_format_4_isolated(self):
        """Test Format 4 in isolation"""
        print("🔍 Testing Format 4 in isolation...")
        
        # Test the exact line that's missing
        test_data = "70.171.218.52:admin:admin:US:Arizona:85001"
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            print(f"📊 Results: Added: {report.get('added', 0)}, Errors: {report.get('format_errors', 0)}")
            
            if report.get('format_errors', 0) > 0:
                print("❌ Format errors detected!")
                if 'details' in report and 'format_errors' in report['details']:
                    for error in report['details']['format_errors']:
                        print(f"   Error: {error}")
            
            if report.get('added', 0) > 0:
                print("✅ Node created successfully")
            else:
                print("❌ No nodes created")
                
            return report.get('added', 0) > 0
        else:
            print(f"❌ Request failed: {response}")
            return False

    def test_problematic_section(self):
        """Test the problematic section from user data"""
        print("\n🔍 Testing problematic section...")
        
        # The section containing the missing node
        test_data = """PPTP INFINITY
@pptpinfinity_bot
70.171.218.52:admin:admin:US:Arizona:85001"""
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            print(f"📊 Results: Added: {report.get('added', 0)}, Processed: {report.get('total_processed', 0)}, Parsed: {report.get('successfully_parsed', 0)}")
            
            if report.get('format_errors', 0) > 0:
                print("❌ Format errors detected!")
                if 'details' in report and 'format_errors' in report['details']:
                    for error in report['details']['format_errors']:
                        print(f"   Error: {error}")
            
            return report.get('added', 0) > 0
        else:
            print(f"❌ Request failed: {response}")
            return False

def main():
    tester = FormatTester()
    if tester.login():
        tester.test_format_4_isolated()
        tester.test_problematic_section()

if __name__ == "__main__":
    main()