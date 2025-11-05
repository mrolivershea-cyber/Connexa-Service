#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class DeduplicationTester:
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
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False

    def make_request(self, method, endpoint, data=None):
        """Make API request"""
        url = f"{self.api_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            return response.status_code == 200, response.json() if response.headers.get('content-type', '').startswith('application/json') else {"text": response.text, "status_code": response.status_code}

        except Exception as e:
            return False, {"error": str(e)}

    def test_small_file_with_duplicates(self):
        """Test with smaller file containing known duplicates"""
        print("\n🚨 CRITICAL TEST: Small file with known duplicates")
        
        # Read the small test file
        try:
            with open('/tmp/pptp_small_test.txt', 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            print(f"❌ Failed to read test file: {e}")
            return False
        
        print(f"📄 File size: {len(file_content)} characters")
        print(f"📄 File lines: {len(file_content.split(chr(10)))}")
        
        import_data = {
            "data": file_content,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            print(f"📊 IMPORT RESULTS:")
            print(f"   Total processed: {report.get('total_processed', 0)}")
            print(f"   Added: {report.get('added', 0)}")
            print(f"   Skipped duplicates: {report.get('skipped_duplicates', 0)}")
            print(f"   Format errors: {report.get('format_errors', 0)}")
            print(f"   Success: {response.get('success', False)}")
            
            # Check for specific IP
            success2, response2 = self.make_request('GET', 'nodes', {'ip': '98.127.101.184'})
            if success2 and 'nodes' in response2:
                count = len(response2['nodes'])
                print(f"   98.127.101.184 instances in DB: {count}")
                
                if count == 1:
                    print("✅ SUCCESS: Deduplication working - only 1 instance of duplicate IP")
                    return True
                else:
                    print(f"❌ FAILED: Expected 1 instance, found {count}")
                    return False
            else:
                print(f"❌ FAILED: Could not check IP: {response2}")
                return False
        else:
            print(f"❌ FAILED: Import failed: {response}")
            return False

    def test_re_import_same_data(self):
        """Test re-importing the same data"""
        print("\n🚨 CRITICAL TEST: Re-import same data")
        
        # Read the same file again
        try:
            with open('/tmp/pptp_small_test.txt', 'r', encoding='utf-8') as f:
                file_content = f.read()
        except Exception as e:
            print(f"❌ Failed to read test file: {e}")
            return False
        
        import_data = {
            "data": file_content,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            print(f"📊 RE-IMPORT RESULTS:")
            print(f"   Added: {report.get('added', 0)}")
            print(f"   Skipped duplicates: {report.get('skipped_duplicates', 0)}")
            print(f"   Success: {response.get('success', False)}")
            
            if response.get('success', False) and report.get('added', 0) == 0:
                print("✅ SUCCESS: Re-import successful with 0 added (all skipped as duplicates)")
                return True
            else:
                print(f"❌ FAILED: Re-import should add 0 nodes, added {report.get('added', 0)}")
                return False
        else:
            print(f"❌ FAILED: Re-import failed: {response}")
            return False

    def test_within_import_deduplication(self):
        """Test deduplication within a single import"""
        print("\n🚨 CRITICAL TEST: Within-import deduplication")
        
        # Create data with duplicates within the same import
        duplicate_data = """Ip: 192.168.100.1
Login: testuser
Pass: testpass
State: CA

Ip: 192.168.100.2
Login: testuser2
Pass: testpass2
State: NY

Ip: 192.168.100.1
Login: testuser
Pass: testpass
State: CA"""

        import_data = {
            "data": duplicate_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            print(f"📊 WITHIN-IMPORT DEDUPLICATION RESULTS:")
            print(f"   Total processed: {report.get('total_processed', 0)}")
            print(f"   Added: {report.get('added', 0)}")
            print(f"   Skipped duplicates: {report.get('skipped_duplicates', 0)}")
            
            # Should process 3 blocks but only add 2 (1 duplicate within import)
            if (report.get('total_processed', 0) == 3 and 
                report.get('added', 0) == 2 and 
                report.get('skipped_duplicates', 0) == 1):
                print("✅ SUCCESS: Within-import deduplication working correctly")
                return True
            else:
                print(f"❌ FAILED: Expected 3 processed, 2 added, 1 skipped")
                return False
        else:
            print(f"❌ FAILED: Import failed: {response}")
            return False

    def run_all_tests(self):
        """Run all deduplication tests"""
        print("🚨 CRITICAL DEDUPLICATION TESTING")
        print("=" * 50)
        
        if not self.login():
            return False
        
        # Test 1: Small file with duplicates
        test1 = self.test_small_file_with_duplicates()
        
        # Test 2: Re-import same data
        test2 = self.test_re_import_same_data()
        
        # Test 3: Within-import deduplication
        test3 = self.test_within_import_deduplication()
        
        print("\n" + "=" * 50)
        print("🏁 DEDUPLICATION TEST SUMMARY:")
        print(f"   Small file test: {'✅ PASSED' if test1 else '❌ FAILED'}")
        print(f"   Re-import test: {'✅ PASSED' if test2 else '❌ FAILED'}")
        print(f"   Within-import test: {'✅ PASSED' if test3 else '❌ FAILED'}")
        
        overall = test1 and test2 and test3
        print(f"   OVERALL: {'✅ ALL TESTS PASSED' if overall else '❌ SOME TESTS FAILED'}")
        print("=" * 50)
        
        return overall

if __name__ == "__main__":
    tester = DeduplicationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)