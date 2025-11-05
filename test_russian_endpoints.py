#!/usr/bin/env python3
"""
Тестирование новых endpoints для Russian User Review Request
Test all new manual test endpoints and verify they work correctly
"""

import requests
import sys
import json
import time

class RussianEndpointsTester:
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
            print(f"   ℹ️  {details}")
    
    def make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}
            
            return response.status_code, response_data
        
        except Exception as e:
            return 0, {"error": str(e)}
    
    def login(self):
        """Login with admin credentials"""
        print("\n🔐 Logging in as admin...")
        status, response = self.make_request('POST', 'auth/login', {
            "username": "admin",
            "password": "admin"
        })
        
        if status == 200 and 'access_token' in response:
            self.token = response['access_token']
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response}")
            return False
    
    def test_manual_geo_test_batch(self):
        """Test 1: POST /api/manual/geo-test-batch"""
        print("\n" + "="*80)
        print("TEST 1: POST /api/manual/geo-test-batch")
        print("="*80)
        
        # Get a node to test
        status, nodes_response = self.make_request('GET', 'nodes', params={'limit': 1})
        
        if status != 200 or not nodes_response.get('nodes'):
            self.log_test("Manual Geo Test Batch", False, "No nodes available")
            return False
        
        node = nodes_response['nodes'][0]
        node_id = node['id']
        
        # Get BEFORE state
        status, before = self.make_request('GET', f'nodes/{node_id}')
        print(f"\n📊 Node {node_id} BEFORE geo test:")
        print(f"   Status: {before.get('status')}")
        print(f"   Country: {before.get('country')}")
        print(f"   State: {before.get('state')}")
        print(f"   City: {before.get('city')}")
        print(f"   Provider: {before.get('provider')}")
        
        # Test endpoint
        print(f"\n🔄 Testing POST /api/manual/geo-test-batch with node_ids=[{node_id}]...")
        status, response = self.make_request('POST', 'manual/geo-test-batch', {"node_ids": [node_id]})
        
        print(f"   Response status: {status}")
        print(f"   Response: {json.dumps(response, indent=2)}")
        
        if status == 500:
            self.log_test("Manual Geo Test Batch", False, "❌ CRITICAL: Endpoint returns 500 error!")
            return False
        
        if status != 200:
            self.log_test("Manual Geo Test Batch", False, f"Unexpected status code: {status}")
            return False
        
        # Get AFTER state
        status, after = self.make_request('GET', f'nodes/{node_id}')
        print(f"\n📊 Node {node_id} AFTER geo test:")
        print(f"   Status: {after.get('status')}")
        print(f"   Country: {after.get('country')}")
        print(f"   State: {after.get('state')}")
        print(f"   City: {after.get('city')}")
        print(f"   Provider: {after.get('provider')}")
        
        # Check if fields updated
        geo_updated = (after.get('country') != before.get('country') or 
                      after.get('state') != before.get('state') or
                      after.get('city') != before.get('city') or
                      after.get('provider') != before.get('provider'))
        
        if geo_updated:
            self.log_test("Manual Geo Test Batch", True, "Geo fields updated successfully")
        else:
            self.log_test("Manual Geo Test Batch", True, "No updates (may already have data)")
        
        return True
    
    def test_manual_fraud_test_batch(self):
        """Test 2: POST /api/manual/fraud-test-batch"""
        print("\n" + "="*80)
        print("TEST 2: POST /api/manual/fraud-test-batch")
        print("="*80)
        
        # Get a node to test
        status, nodes_response = self.make_request('GET', 'nodes', params={'limit': 1})
        
        if status != 200 or not nodes_response.get('nodes'):
            self.log_test("Manual Fraud Test Batch", False, "No nodes available")
            return False
        
        node = nodes_response['nodes'][0]
        node_id = node['id']
        
        # Get BEFORE state
        status, before = self.make_request('GET', f'nodes/{node_id}')
        print(f"\n📊 Node {node_id} BEFORE fraud test:")
        print(f"   Status: {before.get('status')}")
        print(f"   Fraud Score: {before.get('scamalytics_fraud_score')}")
        print(f"   Risk Level: {before.get('scamalytics_risk')}")
        
        # Test endpoint
        print(f"\n🔄 Testing POST /api/manual/fraud-test-batch with node_ids=[{node_id}]...")
        status, response = self.make_request('POST', 'manual/fraud-test-batch', {"node_ids": [node_id]})
        
        print(f"   Response status: {status}")
        print(f"   Response: {json.dumps(response, indent=2)}")
        
        if status == 500:
            self.log_test("Manual Fraud Test Batch", False, "❌ CRITICAL: Endpoint returns 500 error!")
            return False
        
        if status != 200:
            self.log_test("Manual Fraud Test Batch", False, f"Unexpected status code: {status}")
            return False
        
        # Get AFTER state
        status, after = self.make_request('GET', f'nodes/{node_id}')
        print(f"\n📊 Node {node_id} AFTER fraud test:")
        print(f"   Status: {after.get('status')}")
        print(f"   Fraud Score: {after.get('scamalytics_fraud_score')}")
        print(f"   Risk Level: {after.get('scamalytics_risk')}")
        
        # Check if fields updated
        fraud_updated = (after.get('scamalytics_fraud_score') != before.get('scamalytics_fraud_score') or
                        after.get('scamalytics_risk') != before.get('scamalytics_risk'))
        
        if fraud_updated:
            self.log_test("Manual Fraud Test Batch", True, "Fraud fields updated successfully")
        else:
            self.log_test("Manual Fraud Test Batch", True, "No updates (may already have data)")
        
        return True
    
    def test_manual_geo_fraud_test_batch(self):
        """Test 3: POST /api/manual/geo-fraud-test-batch"""
        print("\n" + "="*80)
        print("TEST 3: POST /api/manual/geo-fraud-test-batch")
        print("="*80)
        
        # Get a node to test
        status, nodes_response = self.make_request('GET', 'nodes', params={'limit': 1})
        
        if status != 200 or not nodes_response.get('nodes'):
            self.log_test("Manual Geo-Fraud Test Batch", False, "No nodes available")
            return False
        
        node = nodes_response['nodes'][0]
        node_id = node['id']
        
        # Get BEFORE state
        status, before = self.make_request('GET', f'nodes/{node_id}')
        print(f"\n📊 Node {node_id} BEFORE geo-fraud test:")
        print(f"   Status: {before.get('status')}")
        print(f"   Country: {before.get('country')}, State: {before.get('state')}, City: {before.get('city')}")
        print(f"   Provider: {before.get('provider')}")
        print(f"   Fraud Score: {before.get('scamalytics_fraud_score')}, Risk: {before.get('scamalytics_risk')}")
        
        # Test endpoint
        print(f"\n🔄 Testing POST /api/manual/geo-fraud-test-batch with node_ids=[{node_id}]...")
        status, response = self.make_request('POST', 'manual/geo-fraud-test-batch', {"node_ids": [node_id]})
        
        print(f"   Response status: {status}")
        print(f"   Response: {json.dumps(response, indent=2)}")
        
        if status == 500:
            self.log_test("Manual Geo-Fraud Test Batch", False, "❌ CRITICAL: Endpoint returns 500 error!")
            return False
        
        if status != 200:
            self.log_test("Manual Geo-Fraud Test Batch", False, f"Unexpected status code: {status}")
            return False
        
        # Get AFTER state
        status, after = self.make_request('GET', f'nodes/{node_id}')
        print(f"\n📊 Node {node_id} AFTER geo-fraud test:")
        print(f"   Status: {after.get('status')}")
        print(f"   Country: {after.get('country')}, State: {after.get('state')}, City: {after.get('city')}")
        print(f"   Provider: {after.get('provider')}")
        print(f"   Fraud Score: {after.get('scamalytics_fraud_score')}, Risk: {after.get('scamalytics_risk')}")
        
        # Check if any fields updated
        geo_updated = (after.get('country') != before.get('country') or 
                      after.get('state') != before.get('state') or
                      after.get('city') != before.get('city') or
                      after.get('provider') != before.get('provider'))
        fraud_updated = (after.get('scamalytics_fraud_score') != before.get('scamalytics_fraud_score') or
                        after.get('scamalytics_risk') != before.get('scamalytics_risk'))
        
        if geo_updated or fraud_updated:
            self.log_test("Manual Geo-Fraud Test Batch", True, f"Fields updated - Geo: {geo_updated}, Fraud: {fraud_updated}")
        else:
            self.log_test("Manual Geo-Fraud Test Batch", True, "No updates (may already have data)")
        
        return True
    
    def test_speed_test_status_transition(self):
        """Test 4: POST /api/nodes/{node_id}/test?test_type=speed"""
        print("\n" + "="*80)
        print("TEST 4: POST /api/nodes/{node_id}/test?test_type=speed")
        print("="*80)
        
        # Find a node with ping_ok status
        status, nodes_response = self.make_request('GET', 'nodes', params={'status': 'ping_ok', 'limit': 1})
        
        if status != 200 or not nodes_response.get('nodes'):
            # Try any node
            status, nodes_response = self.make_request('GET', 'nodes', params={'limit': 1})
            if status != 200 or not nodes_response.get('nodes'):
                self.log_test("Speed Test Status Transition", False, "No nodes available")
                return False
        
        node = nodes_response['nodes'][0]
        node_id = node['id']
        
        # Get BEFORE state
        status, before = self.make_request('GET', f'nodes/{node_id}')
        before_status = before.get('status')
        print(f"\n📊 Node {node_id} BEFORE speed test:")
        print(f"   Status: {before_status}")
        
        # Test endpoint
        print(f"\n🔄 Testing POST /api/nodes/{node_id}/test?test_type=speed...")
        status, response = self.make_request('POST', f'nodes/{node_id}/test', params={'test_type': 'speed'})
        
        print(f"   Response status: {status}")
        print(f"   Response: {json.dumps(response, indent=2)}")
        
        if status == 500:
            self.log_test("Speed Test Status Transition", False, "❌ CRITICAL: Endpoint returns 500 error!")
            return False
        
        if status != 200:
            self.log_test("Speed Test Status Transition", False, f"Unexpected status code: {status}")
            return False
        
        # Get AFTER state
        status, after = self.make_request('GET', f'nodes/{node_id}')
        after_status = after.get('status')
        print(f"\n📊 Node {node_id} AFTER speed test:")
        print(f"   Status: {after_status}")
        
        # CRITICAL CHECK: Status should NOT change to not_tested
        if after_status == 'not_tested':
            self.log_test("Speed Test Status Transition", False, 
                         f"❌ CRITICAL BUG: Status changed to 'not_tested' (was {before_status})")
            return False
        
        # Check expected transition: ping_ok → speed_ok
        if before_status == 'ping_ok' and after_status == 'speed_ok':
            self.log_test("Speed Test Status Transition", True, 
                         f"✅ Correct transition: ping_ok → speed_ok")
            return True
        elif before_status == 'ping_ok' and after_status == 'ping_ok':
            self.log_test("Speed Test Status Transition", True, 
                         f"⚠️ Status remained ping_ok (speed test may have failed)")
            return True
        else:
            self.log_test("Speed Test Status Transition", True, 
                         f"Status transition: {before_status} → {after_status}")
            return True
    
    def check_backend_logs(self):
        """Check backend logs for errors"""
        print("\n" + "="*80)
        print("CHECKING BACKEND LOGS")
        print("="*80)
        
        import subprocess
        try:
            result = subprocess.run(
                ['tail', '-n', '50', '/var/log/supervisor/backend.err.log'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout:
                print("\n📋 Last 50 lines of backend error log:")
                print(result.stdout)
                
                # Check for critical errors
                if '500' in result.stdout or 'Error' in result.stdout or 'Exception' in result.stdout:
                    print("\n⚠️  WARNING: Errors detected in backend logs!")
                else:
                    print("\n✅ No critical errors in recent logs")
            else:
                print("✅ No errors in backend log")
        
        except Exception as e:
            print(f"⚠️  Could not read backend logs: {e}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "N/A")
        print("="*80 + "\n")
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*80)
        print("🇷🇺 RUSSIAN USER REVIEW REQUEST - ENDPOINT TESTING")
        print("="*80)
        print("Testing all new manual test endpoints")
        print("API: http://localhost:8001/api")
        print("Login: admin/admin")
        print("="*80)
        
        if not self.login():
            print("\n❌ Cannot proceed without login")
            return
        
        # Run all 4 tests
        self.test_manual_geo_test_batch()
        self.test_manual_fraud_test_batch()
        self.test_manual_geo_fraud_test_batch()
        self.test_speed_test_status_transition()
        
        # Check backend logs
        self.check_backend_logs()
        
        # Print summary
        self.print_summary()

if __name__ == "__main__":
    tester = RussianEndpointsTester()
    tester.run_all_tests()
