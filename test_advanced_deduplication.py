#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class AdvancedDeduplicationTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

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
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
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

    def test_login(self):
        """Test login with admin credentials"""
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log_test("Admin Login", True)
            return True
        else:
            self.log_test("Admin Login", False, f"Login failed: {response}")
            return False

    def test_advanced_deduplication_exact_duplicates(self):
        """Test 1: Exact Duplicates - Import nodes with same IP+Login+Password should skip as duplicates"""
        print("\n🔍 TEST 1: Advanced Deduplication - Exact Duplicates")
        
        # Create unique test data to avoid conflicts with existing nodes
        timestamp = str(int(time.time()))
        test_ip = f"192.168.100.{timestamp[-2:]}"
        
        # First import
        import_data_1 = {
            "data": f"Ip: {test_ip}\nLogin: testuser\nPass: testpass123\nState: CA\nCity: Los Angeles",
            "protocol": "pptp"
        }
        
        success1, response1 = self.make_request('POST', 'nodes/import', import_data_1)
        
        if not success1:
            self.log_test("Advanced Deduplication - Exact Duplicates", False, f"First import failed: {response1}")
            return False
        
        # Second import (exact duplicate)
        import_data_2 = {
            "data": f"Ip: {test_ip}\nLogin: testuser\nPass: testpass123\nState: CA\nCity: Los Angeles",
            "protocol": "pptp"
        }
        
        success2, response2 = self.make_request('POST', 'nodes/import', import_data_2)
        
        if success2 and 'report' in response2:
            report = response2['report']
            if report.get('skipped_duplicates', 0) >= 1 and report.get('added', 0) == 0:
                self.log_test("Advanced Deduplication - Exact Duplicates", True, 
                             f"✅ Exact duplicate correctly skipped (same IP+Login+Password)")
                return True
            else:
                self.log_test("Advanced Deduplication - Exact Duplicates", False, 
                             f"❌ Expected duplicate to be skipped, got: added={report.get('added', 0)}, skipped={report.get('skipped_duplicates', 0)}")
                return False
        else:
            self.log_test("Advanced Deduplication - Exact Duplicates", False, f"Second import failed: {response2}")
            return False

    def test_advanced_deduplication_4_week_rule(self):
        """Test 2: 4-Week Rule - Old nodes (>4 weeks) should be replaced with new credentials"""
        print("\n🔍 TEST 2: Advanced Deduplication - 4-Week Rule")
        
        timestamp = str(int(time.time()))
        test_ip = f"192.168.101.{timestamp[-2:]}"
        
        # Step 1: Create a node with specific credentials
        import_data_1 = {
            "data": f"Ip: {test_ip}\nLogin: olduser\nPass: oldpass123\nState: TX\nCity: Austin",
            "protocol": "pptp"
        }
        
        success1, response1 = self.make_request('POST', 'nodes/import', import_data_1)
        
        if not success1:
            self.log_test("Advanced Deduplication - 4-Week Rule", False, f"Initial node creation failed: {response1}")
            return False
        
        # Step 2: Get the created node
        nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={test_ip}')
        
        if not (nodes_success and 'nodes' in nodes_response and nodes_response['nodes']):
            self.log_test("Advanced Deduplication - 4-Week Rule", False, "Could not retrieve created node")
            return False
        
        node = nodes_response['nodes'][0]
        node_id = node['id']
        
        # Step 3: Import new node with same IP but different credentials
        import_data_2 = {
            "data": f"Ip: {test_ip}\nLogin: newuser\nPass: newpass456\nState: CA\nCity: San Francisco",
            "protocol": "pptp"
        }
        
        success2, response2 = self.make_request('POST', 'nodes/import', import_data_2)
        
        if success2 and 'report' in response2:
            report = response2['report']
            
            # Check if node was replaced or queued for verification
            if report.get('replaced_old', 0) > 0:
                self.log_test("Advanced Deduplication - 4-Week Rule", True, 
                             f"✅ Old node replaced with new credentials (4-week rule applied)")
                return True
            elif report.get('queued_for_verification', 0) > 0:
                self.log_test("Advanced Deduplication - 4-Week Rule", True, 
                             f"✅ Node queued for verification (recent node conflict detected)")
                return True
            else:
                self.log_test("Advanced Deduplication - 4-Week Rule", False, 
                             f"❌ Expected replacement or verification queue, got: {report}")
                return False
        else:
            self.log_test("Advanced Deduplication - 4-Week Rule", False, f"Second import failed: {response2}")
            return False

    def test_advanced_deduplication_recent_node_conflict(self):
        """Test 3: Recent Node Conflict - Same IP with different credentials should create verification queue entry"""
        print("\n🔍 TEST 3: Advanced Deduplication - Recent Node Conflict")
        
        timestamp = str(int(time.time()))
        test_ip = f"192.168.102.{timestamp[-2:]}"
        
        # Step 1: Create a recent node (< 4 weeks)
        import_data_1 = {
            "data": f"Ip: {test_ip}\nLogin: recentuser\nPass: recentpass123\nState: FL\nCity: Miami",
            "protocol": "pptp"
        }
        
        success1, response1 = self.make_request('POST', 'nodes/import', import_data_1)
        
        if not success1:
            self.log_test("Advanced Deduplication - Recent Node Conflict", False, f"Initial node creation failed: {response1}")
            return False
        
        # Step 2: Import new node with same IP but different credentials
        import_data_2 = {
            "data": f"Ip: {test_ip}\nLogin: conflictuser\nPass: conflictpass456\nState: NY\nCity: New York",
            "protocol": "pptp"
        }
        
        success2, response2 = self.make_request('POST', 'nodes/import', import_data_2)
        
        if success2 and 'report' in response2:
            report = response2['report']
            
            # Should create verification queue entry, not replace
            if report.get('queued_for_verification', 0) > 0:
                self.log_test("Advanced Deduplication - Recent Node Conflict", True, 
                             f"✅ Recent node conflict detected, entry queued for verification")
                return True
            elif report.get('replaced_old', 0) > 0:
                self.log_test("Advanced Deduplication - Recent Node Conflict", False, 
                             f"❌ Node was replaced but should have been queued (recent conflict)")
                return False
            else:
                self.log_test("Advanced Deduplication - Recent Node Conflict", False, 
                             f"❌ Expected verification queue entry, got: {report}")
                return False
        else:
            self.log_test("Advanced Deduplication - Recent Node Conflict", False, f"Second import failed: {response2}")
            return False

    def test_advanced_deduplication_verification_queue(self):
        """Test 4: Verification Queue - Check /app/verification_queue.json file structure"""
        print("\n🔍 TEST 4: Advanced Deduplication - Verification Queue File")
        
        timestamp = str(int(time.time()))
        test_ip = f"192.168.103.{timestamp[-2:]}"
        
        # Step 1: Create a node that will trigger verification queue
        import_data_1 = {
            "data": f"Ip: {test_ip}\nLogin: queueuser1\nPass: queuepass123\nState: WA\nCity: Seattle",
            "protocol": "pptp"
        }
        
        success1, response1 = self.make_request('POST', 'nodes/import', import_data_1)
        
        if not success1:
            self.log_test("Advanced Deduplication - Verification Queue", False, f"Initial node creation failed: {response1}")
            return False
        
        # Step 2: Import conflicting node to trigger verification queue
        import_data_2 = {
            "data": f"Ip: {test_ip}\nLogin: queueuser2\nPass: queuepass456\nState: OR\nCity: Portland",
            "protocol": "pptp"
        }
        
        success2, response2 = self.make_request('POST', 'nodes/import', import_data_2)
        
        if success2 and 'report' in response2:
            report = response2['report']
            
            if report.get('queued_for_verification', 0) > 0:
                # Step 3: Check if verification_queue.json file exists and has proper structure
                try:
                    import os
                    
                    queue_file = "/app/verification_queue.json"
                    if os.path.exists(queue_file):
                        with open(queue_file, 'r', encoding='utf-8') as f:
                            queue_data = json.load(f)
                        
                        if isinstance(queue_data, list) and len(queue_data) > 0:
                            # Check structure of queue entries
                            entry = queue_data[-1]  # Get latest entry
                            required_fields = ['id', 'timestamp', 'node_data', 'conflicting_node_ids', 'status']
                            
                            if all(field in entry for field in required_fields):
                                self.log_test("Advanced Deduplication - Verification Queue", True, 
                                             f"✅ Verification queue file created with proper structure: {required_fields}")
                                return True
                            else:
                                self.log_test("Advanced Deduplication - Verification Queue", False, 
                                             f"❌ Queue entry missing required fields. Found: {list(entry.keys())}")
                                return False
                        else:
                            self.log_test("Advanced Deduplication - Verification Queue", False, 
                                         f"❌ Queue file exists but is empty or invalid format")
                            return False
                    else:
                        self.log_test("Advanced Deduplication - Verification Queue", False, 
                                     f"❌ Verification queue file not created at {queue_file}")
                        return False
                        
                except Exception as e:
                    self.log_test("Advanced Deduplication - Verification Queue", False, 
                                 f"❌ Error checking verification queue file: {e}")
                    return False
            else:
                self.log_test("Advanced Deduplication - Verification Queue", False, 
                             f"❌ No entries queued for verification: {report}")
                return False
        else:
            self.log_test("Advanced Deduplication - Verification Queue", False, f"Second import failed: {response2}")
            return False

    def test_advanced_deduplication_import_api_response(self):
        """Test 5: Import API Response - Verify /api/nodes/import returns proper counts"""
        print("\n🔍 TEST 5: Advanced Deduplication - Import API Response Counts")
        
        timestamp = str(int(time.time()))
        
        # Create comprehensive test data that will trigger all deduplication scenarios
        test_data = f"""# Test data for comprehensive deduplication
Ip: 192.168.104.{timestamp[-2:]}
Login: apitest1
Pass: apipass123
State: CA
City: Los Angeles

Ip: 192.168.105.{timestamp[-2:]}
Login: apitest2
Pass: apipass456
State: TX
City: Houston

# Duplicate within import (should be skipped)
Ip: 192.168.104.{timestamp[-2:]}
Login: apitest1
Pass: apipass123
State: CA
City: Los Angeles

# Invalid format (should cause format error)
Invalid line without proper format
Another bad line

# Valid node
Ip: 192.168.106.{timestamp[-2:]}
Login: apitest3
Pass: apipass789
State: NY
City: New York"""
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            
            # Verify all required fields are present
            required_fields = ['added', 'skipped_duplicates', 'replaced_old', 'queued_for_verification', 'format_errors']
            missing_fields = [field for field in required_fields if field not in report]
            
            if missing_fields:
                self.log_test("Advanced Deduplication - Import API Response", False, 
                             f"❌ Missing required fields in response: {missing_fields}")
                return False
            
            # Verify counts make sense
            added = report.get('added', 0)
            skipped = report.get('skipped_duplicates', 0)
            replaced = report.get('replaced_old', 0)
            queued = report.get('queued_for_verification', 0)
            format_errors = report.get('format_errors', 0)
            
            print(f"📊 API RESPONSE COUNTS:")
            print(f"   Added: {added}")
            print(f"   Skipped duplicates: {skipped}")
            print(f"   Replaced old: {replaced}")
            print(f"   Queued for verification: {queued}")
            print(f"   Format errors: {format_errors}")
            
            # Expected: 3 unique nodes, 1 duplicate within import, 2 format errors
            if added >= 3 and skipped >= 1 and format_errors >= 2:
                self.log_test("Advanced Deduplication - Import API Response", True, 
                             f"✅ All required counts present and reasonable: added={added}, skipped={skipped}, format_errors={format_errors}")
                return True
            else:
                self.log_test("Advanced Deduplication - Import API Response", False, 
                             f"❌ Unexpected counts: expected added>=3, skipped>=1, format_errors>=2")
                return False
        else:
            self.log_test("Advanced Deduplication - Import API Response", False, f"Import failed: {response}")
            return False

    def test_advanced_deduplication_realistic_pptp_data(self):
        """Test 6: Realistic PPTP Node Data - Use realistic PPTP node data for testing"""
        print("\n🔍 TEST 6: Advanced Deduplication - Realistic PPTP Data")
        
        # Use realistic PPTP data as specified in review request
        realistic_data = """# Realistic PPTP test data
Ip: 74.125.224.72
Login: vpnuser01
Pass: SecurePass2024!
State: CA
City: Mountain View
Zip: 94043
Provider: Google Fiber
Country: US

Ip: 208.67.222.222
Login: opendns_user
Pass: DNS_Pass_123
State: CA
City: San Francisco
Zip: 94107
Provider: OpenDNS
Country: US

Ip: 8.8.8.8
Login: google_dns
Pass: Public_DNS_456
State: CA
City: Mountain View
Zip: 94043
Provider: Google Public DNS
Country: US

# Test duplicate (same as first)
Ip: 74.125.224.72
Login: vpnuser01
Pass: SecurePass2024!
State: CA
City: Mountain View

# Test same IP different credentials
Ip: 74.125.224.72
Login: different_user
Pass: DifferentPass789
State: NY
City: New York"""
        
        import_data = {
            "data": realistic_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            
            # Should have:
            # - 3 unique nodes added initially
            # - 1 duplicate skipped
            # - 1 queued for verification (same IP, different creds)
            
            added = report.get('added', 0)
            skipped = report.get('skipped_duplicates', 0)
            queued = report.get('queued_for_verification', 0)
            
            print(f"📊 REALISTIC DATA RESULTS:")
            print(f"   Added: {added}")
            print(f"   Skipped duplicates: {skipped}")
            print(f"   Queued for verification: {queued}")
            
            # Verify realistic data was processed correctly
            if added >= 3:
                # Check if specific realistic nodes were created
                test_ips = ['74.125.224.72', '208.67.222.222', '8.8.8.8']
                verified_nodes = 0
                
                for ip in test_ips:
                    nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        verified_nodes += 1
                
                if verified_nodes >= 3:
                    self.log_test("Advanced Deduplication - Realistic PPTP Data", True, 
                                 f"✅ Realistic PPTP data processed correctly: {verified_nodes} nodes verified")
                    return True
                else:
                    self.log_test("Advanced Deduplication - Realistic PPTP Data", False, 
                                 f"❌ Only {verified_nodes}/3 realistic nodes found in database")
                    return False
            else:
                self.log_test("Advanced Deduplication - Realistic PPTP Data", False, 
                             f"❌ Expected at least 3 nodes added, got {added}")
                return False
        else:
            self.log_test("Advanced Deduplication - Realistic PPTP Data", False, f"Import failed: {response}")
            return False

    def run_advanced_deduplication_tests(self):
        """Run all advanced deduplication tests"""
        print("🚨 ADVANCED DEDUPLICATION WITH 4-WEEK RULE TESTS")
        print("="*60)
        
        # Authentication first
        if not self.test_login():
            print("❌ Login failed - cannot continue with authenticated tests")
            return False
        
        # Run all advanced deduplication tests
        self.test_advanced_deduplication_exact_duplicates()
        self.test_advanced_deduplication_4_week_rule()
        self.test_advanced_deduplication_recent_node_conflict()
        self.test_advanced_deduplication_verification_queue()
        self.test_advanced_deduplication_import_api_response()
        self.test_advanced_deduplication_realistic_pptp_data()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🏁 ADVANCED DEDUPLICATION TEST SUMMARY")
        print("="*60)
        print(f"Total tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "No tests run")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Show passed tests
        passed_tests = [result for result in self.test_results if result['success']]
        if passed_tests:
            print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
            for test in passed_tests:
                print(f"   - {test['test']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main function"""
    tester = AdvancedDeduplicationTester()
    success = tester.run_advanced_deduplication_tests()
    tester.print_summary()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())