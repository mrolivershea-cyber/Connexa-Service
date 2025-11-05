#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class Format7Tester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        if details and success:
            print(f"   {details}")

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
            print("✅ Logged in successfully")
            return True
        else:
            print(f"❌ Login failed: {response}")
            return False

    def test_format_7_detection(self):
        """Test 1: Format Detection Test - verify detect_format() returns 'format_7'"""
        print("\n🔍 Test 1: Format Detection Test")
        print("Testing data: '5.78.0.0:admin:admin'")
        
        # Use unique timestamp to avoid duplicates (ensure valid IP)
        timestamp = str(int(time.time()))
        ip_part = int(timestamp[-3:]) % 255  # Ensure IP octet is valid (0-255)
        test_data = f"5.78.{ip_part}.1:admin:admin"
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            if report.get('added', 0) >= 1:
                # Verify the node was created correctly with Format 7 parsing
                ip = f"5.78.{ip_part}.1"
                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    if (node.get('ip') == ip and 
                        node.get('login') == 'admin' and 
                        node.get('password') == 'admin' and
                        not node.get('country') and  # Should be empty for Format 7
                        not node.get('state') and    # Should be empty for Format 7
                        not node.get('zipcode')):    # Should be empty for Format 7
                        self.log_test("Format 7 Detection", True, 
                                     f"Format 7 detected and parsed correctly: IP={node['ip']}, Login={node['login']}, Password={node['password']}, no country/state/zip fields")
                        return True
                    else:
                        self.log_test("Format 7 Detection", False, 
                                     f"Format 7 parsing incorrect. Expected IP={ip}, Login=admin, Password=admin, no location fields. Got: {dict((k,node.get(k)) for k in ['ip','login','password','country','state','zipcode'])}")
                        return False
                else:
                    self.log_test("Format 7 Detection", False, "Node not found after import")
                    return False
            else:
                self.log_test("Format 7 Detection", False, f"No nodes added: {report}")
                return False
        else:
            self.log_test("Format 7 Detection", False, f"Failed to import Format 7 data: {response}")
            return False

    def test_format_7_parsing(self):
        """Test 2: Format Parsing Test - verify both nodes parse correctly"""
        print("\n🔍 Test 2: Format Parsing Test")
        print("Testing data: '144.229.29.35:user:password123\\n76.178.64.46:admin:secret456'")
        
        # Use unique IPs to avoid duplicates (ensure valid IP)
        timestamp = str(int(time.time()))
        ip_part = int(timestamp[-3:]) % 255  # Ensure IP octet is valid (0-255)
        test_data = f"144.229.{ip_part}.35:user:password123\n76.178.{ip_part}.46:admin:secret456"
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            if report.get('added', 0) >= 2:
                # Verify first node
                ip1 = f"144.229.{ip_part}.35"
                ip2 = f"76.178.{ip_part}.46"
                
                nodes_success1, nodes_response1 = self.make_request('GET', f'nodes?ip={ip1}')
                nodes_success2, nodes_response2 = self.make_request('GET', f'nodes?ip={ip2}')
                
                node1_correct = False
                node2_correct = False
                
                if nodes_success1 and 'nodes' in nodes_response1 and nodes_response1['nodes']:
                    node1 = nodes_response1['nodes'][0]
                    if (node1.get('ip') == ip1 and 
                        node1.get('login') == 'user' and 
                        node1.get('password') == 'password123' and
                        not node1.get('country') and not node1.get('state') and not node1.get('zipcode')):
                        node1_correct = True
                
                if nodes_success2 and 'nodes' in nodes_response2 and nodes_response2['nodes']:
                    node2 = nodes_response2['nodes'][0]
                    if (node2.get('ip') == ip2 and 
                        node2.get('login') == 'admin' and 
                        node2.get('password') == 'secret456' and
                        not node2.get('country') and not node2.get('state') and not node2.get('zipcode')):
                        node2_correct = True
                
                if node1_correct and node2_correct:
                    self.log_test("Format 7 Parsing", True, 
                                 f"Both Format 7 nodes parsed correctly with IP, login, password fields. NO country/state/zip fields set as expected")
                    return True
                else:
                    self.log_test("Format 7 Parsing", False, 
                                 f"Format 7 parsing failed. Node1 correct: {node1_correct}, Node2 correct: {node2_correct}")
                    return False
            else:
                self.log_test("Format 7 Parsing", False, f"Expected 2 nodes, got {report.get('added', 0)}")
                return False
        else:
            self.log_test("Format 7 Parsing", False, f"Failed to import Format 7 data: {response}")
            return False

    def test_format_7_small_batch_import(self):
        """Test 3: Small Batch Import Test - import 10 nodes from Format 7"""
        print("\n🔍 Test 3: Small Batch Import Test")
        print("Testing import of 10 nodes in Format 7")
        
        # Generate 10 test nodes in Format 7 with unique IPs
        timestamp = str(int(time.time()))
        ip_part = int(timestamp[-3:]) % 255  # Ensure IP octet is valid (0-255)
        test_nodes = []
        for i in range(10):
            test_nodes.append(f"10.{ip_part}.{i}.{i+1}:user{i}:pass{i}")
        
        test_data = "\n".join(test_nodes)
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            if report.get('added', 0) >= 10:
                # Verify all nodes have 'not_tested' status
                verified_count = 0
                for i in range(10):
                    ip = f"10.{ip_part}.{i}.{i+1}"
                    nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        if (node.get('status') == 'not_tested' and 
                            node.get('login') == f'user{i}' and 
                            node.get('password') == f'pass{i}'):
                            verified_count += 1
                
                if verified_count >= 10:
                    self.log_test("Format 7 Small Batch Import", True, 
                                 f"All 10 Format 7 nodes imported successfully with status='not_tested'")
                    return True
                else:
                    self.log_test("Format 7 Small Batch Import", False, 
                                 f"Only {verified_count}/10 nodes verified correctly")
                    return False
            else:
                self.log_test("Format 7 Small Batch Import", False, f"Expected 10 nodes, got {report.get('added', 0)}")
                return False
        else:
            self.log_test("Format 7 Small Batch Import", False, f"Failed to import Format 7 batch: {response}")
            return False

    def test_format_7_vs_format_4_differentiation(self):
        """Test 4: Format Differentiation Test - ensure Format 7 doesn't conflict with Format 4"""
        print("\n🔍 Test 4: Format Differentiation Test")
        print("Testing both Format 7 (2 colons) and Format 4 (5+ colons) in same import")
        
        # Use unique IPs to avoid duplicates (ensure valid IP)
        timestamp = str(int(time.time()))
        ip_part = int(timestamp[-3:]) % 255  # Ensure IP octet is valid (0-255)
        test_data = f"5.{ip_part}.0.0:admin:admin\n70.{ip_part}.218.52:admin:admin:US:Arizona:85001"
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            if report.get('added', 0) >= 2:
                # Verify Format 7 node (2 colons)
                ip1 = f"5.{ip_part}.0.0"
                ip2 = f"70.{ip_part}.218.52"
                
                nodes_success1, nodes_response1 = self.make_request('GET', f'nodes?ip={ip1}')
                nodes_success2, nodes_response2 = self.make_request('GET', f'nodes?ip={ip2}')
                
                format7_correct = False
                format4_correct = False
                
                if nodes_success1 and 'nodes' in nodes_response1 and nodes_response1['nodes']:
                    node1 = nodes_response1['nodes'][0]
                    # Format 7: should have IP, login, password but NO country/state/zip
                    if (node1.get('ip') == ip1 and 
                        node1.get('login') == 'admin' and 
                        node1.get('password') == 'admin' and
                        not node1.get('country') and not node1.get('state') and not node1.get('zipcode')):
                        format7_correct = True
                
                if nodes_success2 and 'nodes' in nodes_response2 and nodes_response2['nodes']:
                    node2 = nodes_response2['nodes'][0]
                    # Format 4: should have IP, login, password AND country/state/zip
                    if (node2.get('ip') == ip2 and 
                        node2.get('login') == 'admin' and 
                        node2.get('password') == 'admin' and
                        node2.get('country') == 'United States' and 
                        node2.get('state') == 'Arizona' and 
                        node2.get('zipcode') == '85001'):
                        format4_correct = True
                
                if format7_correct and format4_correct:
                    self.log_test("Format 7 vs Format 4 Differentiation", True, 
                                 f"Format differentiation working: Format 7 (2 colons) parsed without location, Format 4 (5+ colons) parsed with full location")
                    return True
                else:
                    self.log_test("Format 7 vs Format 4 Differentiation", False, 
                                 f"Format differentiation failed. Format 7 correct: {format7_correct}, Format 4 correct: {format4_correct}")
                    return False
            else:
                self.log_test("Format 7 vs Format 4 Differentiation", False, f"Expected 2 nodes, got {report.get('added', 0)}")
                return False
        else:
            self.log_test("Format 7 vs Format 4 Differentiation", False, f"Failed to import mixed format data: {response}")
            return False

    def test_format_7_large_file_simulation(self):
        """Test 5: Large File Import Simulation - import 100-500 nodes in Format 7"""
        print("\n🔍 Test 5: Large File Import Simulation")
        print("Testing import of 200 nodes in Format 7 (simulating large file)")
        
        # Generate 200 test nodes in Format 7 (middle of 100-500 range)
        timestamp = str(int(time.time()))
        ip_part = int(timestamp[-3:]) % 255  # Ensure IP octet is valid (0-255)
        test_nodes = []
        for i in range(200):
            # Use different IP ranges to avoid conflicts
            ip_third = (i // 256) + 100
            ip_fourth = i % 256
            test_nodes.append(f"192.{ip_part}.{ip_third}.{ip_fourth}:bulkuser{i}:bulkpass{i}")
        
        test_data = "\n".join(test_nodes)
        
        import_data = {
            "data": test_data,
            "protocol": "pptp"
        }
        
        # Measure performance
        start_time = time.time()
        success, response = self.make_request('POST', 'nodes/import', import_data)
        end_time = time.time()
        
        import_duration = end_time - start_time
        
        if success and 'report' in response:
            report = response['report']
            added_count = report.get('added', 0)
            
            # Check performance is acceptable (should complete within reasonable time)
            performance_acceptable = import_duration < 60  # Should complete within 60 seconds
            
            if added_count >= 200 and performance_acceptable:
                # Verify database integrity by checking a few random nodes
                sample_indices = [0, 50, 100, 150, 199]
                verified_samples = 0
                
                for idx in sample_indices:
                    ip_third = (idx // 256) + 100
                    ip_fourth = idx % 256
                    ip = f"192.{ip_part}.{ip_third}.{ip_fourth}"
                    
                    nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        if (node.get('login') == f'bulkuser{idx}' and 
                            node.get('password') == f'bulkpass{idx}' and
                            node.get('status') == 'not_tested'):
                            verified_samples += 1
                
                if verified_samples >= 5:
                    self.log_test("Format 7 Large File Simulation", True, 
                                 f"Large import successful: {added_count} nodes imported in {import_duration:.1f}s, database integrity verified")
                    return True
                else:
                    self.log_test("Format 7 Large File Simulation", False, 
                                 f"Database integrity check failed: only {verified_samples}/5 sample nodes verified")
                    return False
            else:
                self.log_test("Format 7 Large File Simulation", False, 
                             f"Large import failed: {added_count} nodes added (expected 200), duration: {import_duration:.1f}s, performance acceptable: {performance_acceptable}")
                return False
        else:
            self.log_test("Format 7 Large File Simulation", False, f"Failed to import large Format 7 file: {response}")
            return False

    def run_all_format_7_tests(self):
        """Run all Format 7 tests"""
        print("🇷🇺 FORMAT 7 TESTING - Russian User Request (IP:Login:Pass)")
        print("=" * 60)
        print("Testing new Format 7 support for simple IP:Login:Pass format")
        print("User provided TEST 3.txt file with 65,536 nodes in format like: 5.78.0.0:admin:admin")
        print("=" * 60)
        
        if not self.login():
            return False
        
        # Run all Format 7 tests
        self.test_format_7_detection()
        self.test_format_7_parsing()
        self.test_format_7_small_batch_import()
        self.test_format_7_vs_format_4_differentiation()
        self.test_format_7_large_file_simulation()
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 FORMAT 7 TESTING COMPLETE")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL FORMAT 7 TESTS PASSED!")
            return True
        else:
            print("⚠️  SOME FORMAT 7 TESTS FAILED")
            return False

if __name__ == "__main__":
    tester = Format7Tester()
    success = tester.run_all_format_7_tests()
    sys.exit(0 if success else 1)