#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class LargeFileTester:
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

    def make_request(self, method, endpoint, data=None, timeout=60):
        """Make API request with timeout"""
        url = f"{self.api_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=data, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=timeout)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            return response.status_code == 200, response.json() if response.headers.get('content-type', '').startswith('application/json') else {"text": response.text, "status_code": response.status_code}

        except Exception as e:
            return False, {"error": str(e)}

    def test_medium_file(self):
        """Test with medium-sized file (1000 lines)"""
        print("\n🚨 CRITICAL TEST: Medium file (1000 lines)")
        
        # Read the medium test file
        try:
            with open('/tmp/pptp_medium_test.txt', 'r', encoding='utf-8') as f:
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
        
        print("⏳ Importing medium file (may take a moment)...")
        success, response = self.make_request('POST', 'nodes/import', import_data, timeout=120)
        
        if success and 'report' in response:
            report = response['report']
            print(f"📊 MEDIUM FILE IMPORT RESULTS:")
            print(f"   Total processed: {report.get('total_processed', 0)}")
            print(f"   Added: {report.get('added', 0)}")
            print(f"   Skipped duplicates: {report.get('skipped_duplicates', 0)}")
            print(f"   Format errors: {report.get('format_errors', 0)}")
            print(f"   Success: {response.get('success', False)}")
            
            # Check that we processed a reasonable number of blocks
            if report.get('total_processed', 0) > 50:
                print("✅ SUCCESS: Medium file processed successfully")
                return True, report
            else:
                print(f"❌ FAILED: Expected more blocks processed")
                return False, report
        else:
            print(f"❌ FAILED: Import failed: {response}")
            return False, None

    def test_full_file_chunked(self):
        """Test full file in chunks to avoid timeout"""
        print("\n🚨 CRITICAL TEST: Full file processing (chunked)")
        
        try:
            with open('/tmp/pptp_test.txt', 'r', encoding='utf-8') as f:
                full_content = f.read()
        except Exception as e:
            print(f"❌ Failed to read full test file: {e}")
            return False
        
        # Split into chunks of ~5000 lines each
        lines = full_content.split('\n')
        chunk_size = 5000
        chunks = [lines[i:i + chunk_size] for i in range(0, len(lines), chunk_size)]
        
        print(f"📄 Full file: {len(lines)} lines, split into {len(chunks)} chunks")
        
        total_added = 0
        total_skipped = 0
        total_processed = 0
        
        for i, chunk in enumerate(chunks):
            chunk_content = '\n'.join(chunk)
            
            import_data = {
                "data": chunk_content,
                "protocol": "pptp"
            }
            
            print(f"⏳ Processing chunk {i+1}/{len(chunks)}...")
            success, response = self.make_request('POST', 'nodes/import', import_data, timeout=120)
            
            if success and 'report' in response:
                report = response['report']
                total_added += report.get('added', 0)
                total_skipped += report.get('skipped_duplicates', 0)
                total_processed += report.get('total_processed', 0)
                
                print(f"   Chunk {i+1}: {report.get('added', 0)} added, {report.get('skipped_duplicates', 0)} skipped")
            else:
                print(f"❌ Chunk {i+1} failed: {response}")
                return False
        
        print(f"📊 FULL FILE RESULTS (CHUNKED):")
        print(f"   Total processed: {total_processed}")
        print(f"   Total added: {total_added}")
        print(f"   Total skipped: {total_skipped}")
        
        # Verify specific duplicate IPs
        duplicate_ips = ['98.127.101.184', '71.65.133.123', '24.227.222.2']
        all_single = True
        
        for ip in duplicate_ips:
            success, response = self.make_request('GET', 'nodes', {'ip': ip})
            if success and 'nodes' in response:
                count = len(response['nodes'])
                print(f"   {ip}: {count} instance(s) in database")
                if count != 1:
                    all_single = False
            else:
                print(f"   {ip}: Failed to check")
                all_single = False
        
        if all_single and total_processed > 400:
            print("✅ SUCCESS: Full file processed successfully with proper deduplication")
            return True
        else:
            print(f"❌ FAILED: Issues with full file processing")
            return False

    def run_tests(self):
        """Run large file tests"""
        print("🚨 LARGE FILE DEDUPLICATION TESTING")
        print("=" * 50)
        
        if not self.login():
            return False
        
        # Test 1: Medium file
        test1, report = self.test_medium_file()
        
        # Test 2: Full file chunked (only if medium file works)
        test2 = False
        if test1:
            test2 = self.test_full_file_chunked()
        else:
            print("⏭️ Skipping full file test due to medium file failure")
        
        print("\n" + "=" * 50)
        print("🏁 LARGE FILE TEST SUMMARY:")
        print(f"   Medium file test: {'✅ PASSED' if test1 else '❌ FAILED'}")
        print(f"   Full file test: {'✅ PASSED' if test2 else '❌ FAILED/SKIPPED'}")
        
        overall = test1 and test2
        print(f"   OVERALL: {'✅ ALL TESTS PASSED' if overall else '❌ SOME TESTS FAILED'}")
        print("=" * 50)
        
        return overall

if __name__ == "__main__":
    tester = LargeFileTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)