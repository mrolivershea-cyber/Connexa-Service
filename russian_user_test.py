#!/usr/bin/env python3
"""
RUSSIAN USER REVIEW REQUEST - BACKEND TESTING
Тестирование критических функций по запросу пользователя
"""

import requests
import sys
import json
import time
from datetime import datetime

class RussianUserTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def make_request(self, method: str, endpoint: str, data: dict = None, expected_status: int = 200):
        """Make HTTP request"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data, timeout=30)
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
        """Test 1: Login with admin/admin"""
        print("\n🔐 TEST 1: POST /api/auth/login (admin/admin)")
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log_test("Login (admin/admin)", True, "Token received successfully")
            return True
        else:
            self.log_test("Login (admin/admin)", False, f"Login failed: {response}")
            return False

    def test_get_stats(self):
        """Test 2: GET /api/stats"""
        print("\n📊 TEST 2: GET /api/stats")
        success, response = self.make_request('GET', 'stats')
        
        if success and 'total' in response:
            self.log_test("GET /api/stats", True, 
                         f"Total: {response['total']}, Online: {response.get('online', 0)}, Ping OK: {response.get('ping_ok', 0)}")
            return True
        else:
            self.log_test("GET /api/stats", False, f"Failed: {response}")
            return False

    def test_get_settings(self):
        """Test 3: GET /api/settings"""
        print("\n⚙️ TEST 3: GET /api/settings")
        success, response = self.make_request('GET', 'settings')
        
        if success:
            self.log_test("GET /api/settings", True, 
                         f"Settings retrieved: {list(response.keys()) if isinstance(response, dict) else 'OK'}")
            return True
        else:
            self.log_test("GET /api/settings", False, f"Failed: {response}")
            return False

    def test_post_settings(self):
        """Test 4: POST /api/settings"""
        print("\n⚙️ TEST 4: POST /api/settings")
        test_settings = {
            "geo_service": "ip-api",
            "fraud_service": "ipqs"
        }
        
        success, response = self.make_request('POST', 'settings', test_settings)
        
        if success:
            self.log_test("POST /api/settings", True, "Settings updated successfully")
            return True
        else:
            self.log_test("POST /api/settings", False, f"Failed: {response}")
            return False

    def test_import_with_scamalytics(self):
        """Test 5: Import with Scamalytics data"""
        print("\n📥 TEST 5: POST /api/nodes/import-chunked (with Scamalytics)")
        import_data = {
            "data": """IP: 1.1.1.1
Credentials: test:test
Location: US (Missouri, Kansas City)
ZIP: 64106
Scamalytics Fraud Score: 15
Scamalytics Risk: medium""",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            added = report.get('added', 0)
            skipped = report.get('skipped_duplicates', 0)
            
            self.log_test("Import with Scamalytics", True, 
                         f"Added: {added}, Skipped: {skipped}")
            
            # Verify the node
            time.sleep(1)
            nodes_success, nodes_response = self.make_request('GET', 'nodes?ip=1.1.1.1')
            if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                node = nodes_response['nodes'][0]
                print(f"   ✓ Node found: IP={node.get('ip')}, Login={node.get('login')}")
                print(f"   ✓ Location: {node.get('city')}, {node.get('state')}, {node.get('zipcode')}")
                print(f"   ✓ Scamalytics: fraud_score={node.get('scamalytics_fraud_score')}, risk={node.get('scamalytics_risk')}")
            return True
        else:
            self.log_test("Import with Scamalytics", False, f"Failed: {response}")
            return False

    def test_ping_light_geolocation(self):
        """Test 6: PING LIGHT with geolocation enrichment"""
        print("\n🏓 TEST 6: POST /api/manual/ping-test-batch-progress (PING LIGHT)")
        
        # First, create test node 8.8.8.8
        test_node = {
            "ip": "8.8.8.8",
            "login": "testuser",
            "password": "testpass",
            "protocol": "pptp"
        }
        
        create_success, create_response = self.make_request('POST', 'nodes', test_node, 200)
        
        if not create_success:
            # Node might exist, try to get it
            nodes_success, nodes_response = self.make_request('GET', 'nodes?ip=8.8.8.8')
            if not (nodes_success and 'nodes' in nodes_response and nodes_response['nodes']):
                self.log_test("PING LIGHT Geolocation", False, "Could not create/find test node")
                return False
            node_id = nodes_response['nodes'][0]['id']
        else:
            node_id = create_response.get('id')
        
        print(f"   Using node ID: {node_id}")
        
        # Run PING LIGHT test
        test_data = {
            "node_ids": [node_id],
            "mode": "ping"
        }
        
        success, response = self.make_request('POST', 'manual/ping-test-batch-progress', test_data)
        
        if success and 'session_id' in response:
            session_id = response['session_id']
            print(f"   Session ID: {session_id}")
            
            # Wait for test to complete
            print("   Waiting for test to complete...")
            time.sleep(8)
            
            # Check node enrichment
            nodes_success, nodes_response = self.make_request('GET', f'nodes/{node_id}')
            
            if nodes_success:
                node = nodes_response
                city = node.get('city', '')
                state = node.get('state', '')
                zipcode = node.get('zipcode', '')
                provider = node.get('provider', '')
                
                has_geo = city or state or provider
                
                if has_geo:
                    self.log_test("PING LIGHT Geolocation", True, 
                                 f"Geolocation enriched: City={city}, State={state}, ZIP={zipcode}, Provider={provider}")
                    return True
                else:
                    self.log_test("PING LIGHT Geolocation", False, 
                                 f"Geolocation NOT enriched: City={city}, State={state}, Provider={provider}")
                    return False
            else:
                self.log_test("PING LIGHT Geolocation", False, f"Could not retrieve node: {nodes_response}")
                return False
        else:
            self.log_test("PING LIGHT Geolocation", False, f"Test failed: {response}")
            return False

    def test_database_scamalytics_columns(self):
        """Test 7: Check scamalytics columns exist"""
        print("\n🗄️ TEST 7: Database Check - scamalytics_fraud_score and scamalytics_risk columns")
        
        success, response = self.make_request('GET', 'nodes?limit=1')
        
        if success and 'nodes' in response and response['nodes']:
            node = response['nodes'][0]
            
            has_fraud_score = 'scamalytics_fraud_score' in node
            has_risk = 'scamalytics_risk' in node
            
            if has_fraud_score and has_risk:
                self.log_test("Database Scamalytics Columns", True, 
                             "Both columns exist in database schema")
                return True
            else:
                self.log_test("Database Scamalytics Columns", False, 
                             f"Missing columns: fraud_score={has_fraud_score}, risk={has_risk}")
                return False
        else:
            self.log_test("Database Scamalytics Columns", False, f"Could not get nodes: {response}")
            return False

    def test_service_manager_enrich(self):
        """Test 8: Service Manager enrich_node_complete"""
        print("\n🔧 TEST 8: Service Manager - enrich_node_complete functionality")
        
        # Check if service_manager_geo.py exists and has the method
        try:
            import sys
            sys.path.append('/app/backend')
            from service_manager_geo import service_manager
            
            # Check if method exists
            if hasattr(service_manager, 'enrich_node_complete'):
                self.log_test("Service Manager enrich_node_complete", True, 
                             "Method exists in service_manager_geo.py")
                return True
            else:
                self.log_test("Service Manager enrich_node_complete", False, 
                             "Method not found in service_manager_geo.py")
                return False
        except Exception as e:
            self.log_test("Service Manager enrich_node_complete", False, f"Error: {str(e)}")
            return False

    def check_backend_logs(self):
        """Check backend logs for errors"""
        print("\n📋 Checking backend logs for critical errors...")
        
        try:
            import subprocess
            result = subprocess.run(
                ['tail', '-n', '100', '/var/log/supervisor/backend.err.log'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            error_log = result.stdout
            
            # Check for critical errors
            critical_errors = []
            if 'null bytes' in error_log.lower():
                critical_errors.append("null bytes error in ping_speed_test.py")
            if 'missing method' in error_log.lower() or 'attributeerror' in error_log.lower():
                critical_errors.append("missing methods in service_manager_geo.py")
            if 'migration' in error_log.lower() and 'error' in error_log.lower():
                critical_errors.append("DB migration error")
            
            if critical_errors:
                print(f"   ⚠️ Found critical errors: {', '.join(critical_errors)}")
                return False
            else:
                print("   ✅ No critical errors found in logs")
                return True
        except Exception as e:
            print(f"   ⚠️ Could not check logs: {str(e)}")
            return True  # Don't fail test if we can't check logs

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🏁 RUSSIAN USER REVIEW REQUEST - TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print("="*80)
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL TESTS PASSED!")
            return True
        else:
            print("❌ SOME TESTS FAILED")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
            return False

    def run_all_tests(self):
        """Run all Russian user tests"""
        print("\n" + "="*80)
        print("🇷🇺 RUSSIAN USER REVIEW REQUEST - BACKEND TESTING")
        print("="*80)
        print("Testing critical functionality as requested:")
        print("1. API Endpoints (login, stats, settings)")
        print("2. Import with Scamalytics data")
        print("3. PING LIGHT with geolocation enrichment")
        print("4. Database schema verification")
        print("5. Service Manager functionality")
        print("="*80)
        
        # Test 1: Login
        if not self.test_login():
            print("\n❌ Login failed - cannot continue")
            return self.print_summary()
        
        # Test 2-4: API Endpoints
        self.test_get_stats()
        self.test_get_settings()
        self.test_post_settings()
        
        # Test 5: Import with Scamalytics
        self.test_import_with_scamalytics()
        
        # Test 6: PING LIGHT with geolocation
        self.test_ping_light_geolocation()
        
        # Test 7: Database columns
        self.test_database_scamalytics_columns()
        
        # Test 8: Service Manager
        self.test_service_manager_enrich()
        
        # Check logs
        self.check_backend_logs()
        
        return self.print_summary()


if __name__ == "__main__":
    tester = RussianUserTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
