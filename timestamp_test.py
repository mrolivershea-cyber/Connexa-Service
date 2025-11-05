#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

class TimestampTester:
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

    def test_create_node_timestamp(self):
        """TEST 1: POST /api/nodes - Check that last_update is set to current time (not "8h ago")"""
        import time
        timestamp = str(int(time.time()))
        
        # Record time before creating node
        before_time = datetime.now()
        
        test_node = {
            "ip": f"203.0.113.{timestamp[-2:]}",
            "login": f"timestamp_test_user_{timestamp}",
            "password": "TimestampTest123!",
            "protocol": "pptp",
            "provider": "TimestampTestProvider",
            "country": "United States",
            "state": "California",
            "city": "Los Angeles",
            "zipcode": "90210",
            "comment": "Timestamp test node"
        }
        
        success, response = self.make_request('POST', 'nodes', test_node, 200)
        
        if success and 'id' in response:
            node_id = response['id']
            
            # Get the created node to check timestamp
            nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={test_node["ip"]}')
            
            if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                node = nodes_response['nodes'][0]
                last_update_str = node.get('last_update')
                
                if last_update_str:
                    try:
                        # Parse the timestamp (assuming ISO format)
                        last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                        
                        # Calculate time difference (should be within a few seconds)
                        time_diff = abs((datetime.now() - last_update).total_seconds())
                        
                        if time_diff <= 10:  # Within 10 seconds is acceptable
                            self.log_test("CREATE NODE TIMESTAMP", True, 
                                         f"✅ NEW NODE TIMESTAMP CORRECT: last_update is {time_diff:.1f}s ago (NOT '8h ago')")
                            return node_id
                        else:
                            self.log_test("CREATE NODE TIMESTAMP", False, 
                                         f"❌ TIMESTAMP ISSUE: last_update is {time_diff:.1f}s ago, expected within 10s")
                            return None
                    except Exception as e:
                        self.log_test("CREATE NODE TIMESTAMP", False, 
                                     f"❌ TIMESTAMP PARSE ERROR: {e}, last_update={last_update_str}")
                        return None
                else:
                    self.log_test("CREATE NODE TIMESTAMP", False, 
                                 f"❌ NO TIMESTAMP: last_update field missing")
                    return None
            else:
                self.log_test("CREATE NODE TIMESTAMP", False, 
                             f"❌ Could not retrieve created node")
                return None
        else:
            self.log_test("CREATE NODE TIMESTAMP", False, f"❌ Failed to create node: {response}")
            return None

    def test_import_nodes_timestamp(self):
        """TEST 2: POST /api/nodes/import - Check that new nodes get current timestamps"""
        import time
        timestamp = str(int(time.time()))
        
        import_data = {
            "data": f"""Ip: 192.168.200.{timestamp[-2:]}
Login: import_timestamp_test_{timestamp}
Pass: ImportTimestampTest123
State: California
City: San Francisco

Ip: 192.168.201.{timestamp[-2:]}
Login: import_timestamp_test2_{timestamp}
Pass: ImportTimestampTest456
State: Texas
City: Austin""",
            "protocol": "pptp",
            "testing_mode": "no_test"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        
        if success and 'report' in response:
            report = response['report']
            if report.get('added', 0) >= 2:
                # Check timestamps for both imported nodes
                nodes_success1, nodes_response1 = self.make_request('GET', f'nodes?ip=192.168.200.{timestamp[-2:]}')
                nodes_success2, nodes_response2 = self.make_request('GET', f'nodes?ip=192.168.201.{timestamp[-2:]}')
                
                timestamps_correct = 0
                timestamp_details = []
                
                for i, (nodes_success, nodes_response) in enumerate([(nodes_success1, nodes_response1), (nodes_success2, nodes_response2)], 1):
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        last_update_str = node.get('last_update')
                        
                        if last_update_str:
                            try:
                                last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                                time_diff = abs((datetime.now() - last_update).total_seconds())
                                
                                if time_diff <= 30:  # Within 30 seconds for import
                                    timestamps_correct += 1
                                    timestamp_details.append(f"Node{i}: {time_diff:.1f}s ago ✅")
                                else:
                                    timestamp_details.append(f"Node{i}: {time_diff:.1f}s ago ❌")
                            except Exception as e:
                                timestamp_details.append(f"Node{i}: Parse error ❌")
                        else:
                            timestamp_details.append(f"Node{i}: No timestamp ❌")
                    else:
                        timestamp_details.append(f"Node{i}: Not found ❌")
                
                if timestamps_correct == 2:
                    self.log_test("IMPORT NODES TIMESTAMP", True, 
                                 f"✅ IMPORT TIMESTAMPS CORRECT: {', '.join(timestamp_details)}")
                    return True
                else:
                    self.log_test("IMPORT NODES TIMESTAMP", False, 
                                 f"❌ IMPORT TIMESTAMP ISSUES: {', '.join(timestamp_details)}")
                    return False
            else:
                self.log_test("IMPORT NODES TIMESTAMP", False, 
                             f"❌ Expected 2 nodes imported, got {report.get('added', 0)}")
                return False
        else:
            self.log_test("IMPORT NODES TIMESTAMP", False, f"❌ Import failed: {response}")
            return False

    def test_get_existing_nodes_timestamp(self):
        """TEST 3: GET /api/nodes - Check that existing nodes have correct timestamps after migration"""
        success, response = self.make_request('GET', 'nodes?limit=5')
        
        if success and 'nodes' in response:
            nodes = response['nodes']
            if nodes:
                valid_timestamps = 0
                timestamp_details = []
                
                for i, node in enumerate(nodes[:3], 1):  # Check first 3 nodes
                    last_update_str = node.get('last_update')
                    ip = node.get('ip', 'unknown')
                    
                    if last_update_str:
                        try:
                            last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                            time_diff = abs((datetime.now() - last_update).total_seconds())
                            
                            # For existing nodes, timestamps should be reasonable (not exactly current, but not "8h ago" either)
                            # After migration, they should have been updated to recent times
                            if time_diff <= 3600:  # Within 1 hour is reasonable after migration
                                valid_timestamps += 1
                                timestamp_details.append(f"{ip}: {time_diff/60:.1f}min ago ✅")
                            else:
                                timestamp_details.append(f"{ip}: {time_diff/3600:.1f}h ago ❌")
                        except Exception as e:
                            timestamp_details.append(f"{ip}: Parse error ❌")
                    else:
                        timestamp_details.append(f"{ip}: No timestamp ❌")
                
                if valid_timestamps >= 2:  # At least 2 out of 3 should have valid timestamps
                    self.log_test("GET EXISTING NODES TIMESTAMP", True, 
                                 f"✅ EXISTING NODE TIMESTAMPS VALID: {', '.join(timestamp_details)}")
                    return True
                else:
                    self.log_test("GET EXISTING NODES TIMESTAMP", False, 
                                 f"❌ EXISTING NODE TIMESTAMP ISSUES: {', '.join(timestamp_details)}")
                    return False
            else:
                self.log_test("GET EXISTING NODES TIMESTAMP", False, 
                             f"❌ No nodes found in database")
                return False
        else:
            self.log_test("GET EXISTING NODES TIMESTAMP", False, f"❌ Failed to get nodes: {response}")
            return False

    def test_manual_ping_test_timestamp(self):
        """TEST 4: POST /api/manual/ping-test - Check that last_update updates after status changes"""
        # First, create a test node with 'not_tested' status
        import time
        timestamp = str(int(time.time()))
        
        test_node = {
            "ip": f"203.0.114.{timestamp[-2:]}",
            "login": f"ping_test_user_{timestamp}",
            "password": "PingTest123!",
            "protocol": "pptp",
            "comment": "Manual ping test node"
        }
        
        create_success, create_response = self.make_request('POST', 'nodes', test_node, 200)
        
        if create_success and 'id' in create_response:
            node_id = create_response['id']
            
            # Get initial timestamp
            initial_success, initial_response = self.make_request('GET', f'nodes?ip={test_node["ip"]}')
            
            if initial_success and 'nodes' in initial_response and initial_response['nodes']:
                initial_node = initial_response['nodes'][0]
                initial_timestamp_str = initial_node.get('last_update')
                initial_status = initial_node.get('status')
                
                # Wait a moment to ensure timestamp difference
                time.sleep(2)
                
                # Perform manual ping test
                ping_data = {
                    "node_ids": [node_id]
                }
                
                ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
                
                if ping_success:
                    # Get updated node to check timestamp
                    updated_success, updated_response = self.make_request('GET', f'nodes?ip={test_node["ip"]}')
                    
                    if updated_success and 'nodes' in updated_response and updated_response['nodes']:
                        updated_node = updated_response['nodes'][0]
                        updated_timestamp_str = updated_node.get('last_update')
                        updated_status = updated_node.get('status')
                        
                        if initial_timestamp_str and updated_timestamp_str:
                            try:
                                initial_time = datetime.fromisoformat(initial_timestamp_str.replace('Z', '+00:00'))
                                updated_time = datetime.fromisoformat(updated_timestamp_str.replace('Z', '+00:00'))
                                
                                # Updated timestamp should be more recent than initial
                                if updated_time > initial_time:
                                    time_diff = abs((datetime.now() - updated_time).total_seconds())
                                    
                                    if time_diff <= 10:  # Should be very recent
                                        self.log_test("MANUAL PING TEST TIMESTAMP", True, 
                                                     f"✅ MANUAL PING TIMESTAMP UPDATE: Status '{initial_status}' → '{updated_status}', last_update updated to {time_diff:.1f}s ago")
                                        return True
                                    else:
                                        self.log_test("MANUAL PING TEST TIMESTAMP", False, 
                                                     f"❌ TIMESTAMP NOT CURRENT: Updated timestamp is {time_diff:.1f}s ago, expected within 10s")
                                        return False
                                else:
                                    self.log_test("MANUAL PING TEST TIMESTAMP", False, 
                                                 f"❌ TIMESTAMP NOT UPDATED: Initial={initial_timestamp_str}, Updated={updated_timestamp_str}")
                                    return False
                            except Exception as e:
                                self.log_test("MANUAL PING TEST TIMESTAMP", False, 
                                             f"❌ TIMESTAMP PARSE ERROR: {e}")
                                return False
                        else:
                            self.log_test("MANUAL PING TEST TIMESTAMP", False, 
                                         f"❌ MISSING TIMESTAMPS: Initial={initial_timestamp_str}, Updated={updated_timestamp_str}")
                            return False
                    else:
                        self.log_test("MANUAL PING TEST TIMESTAMP", False, 
                                     f"❌ Could not retrieve updated node")
                        return False
                else:
                    self.log_test("MANUAL PING TEST TIMESTAMP", False, 
                                 f"❌ Manual ping test failed: {ping_response}")
                    return False
            else:
                self.log_test("MANUAL PING TEST TIMESTAMP", False, 
                             f"❌ Could not retrieve initial node")
                return False
        else:
            self.log_test("MANUAL PING TEST TIMESTAMP", False, 
                         f"❌ Failed to create test node: {create_response}")
            return False

    def run_all_timestamp_tests(self):
        """Run all timestamp tests as requested in the review"""
        print("🕐 TIMESTAMP FUNCTIONALITY TESTS (Review Request)")
        print("="*80)
        
        # Test 1: Create new node - timestamp should be current
        print("\n1. Testing POST /api/nodes - new node timestamp...")
        self.test_create_node_timestamp()
        
        # Test 2: Import nodes - timestamps should be current
        print("\n2. Testing POST /api/nodes/import - import timestamp...")
        self.test_import_nodes_timestamp()
        
        # Test 3: Get existing nodes - timestamps should be valid after migration
        print("\n3. Testing GET /api/nodes - existing node timestamps...")
        self.test_get_existing_nodes_timestamp()
        
        # Test 4: Manual ping test - timestamp should update after status change
        print("\n4. Testing POST /api/manual/ping-test - timestamp update...")
        self.test_manual_ping_test_timestamp()
        
        print("\n" + "="*80)
        print("🕐 TIMESTAMP TESTS COMPLETED")
        print("="*80)

if __name__ == "__main__":
    tester = TimestampTester()
    
    print("🚀 Starting Timestamp Testing Suite...")
    print("="*60)
    
    # Test login first
    if not tester.test_login():
        print("❌ Login failed - stopping tests")
        sys.exit(1)
    
    # Run timestamp tests
    tester.run_all_timestamp_tests()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TIMESTAMP TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%" if tester.tests_run > 0 else "No tests run")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All timestamp tests passed!")
        sys.exit(0)
    else:
        print("❌ Some timestamp tests failed!")
        print("\n🔍 Failed tests:")
        for result in tester.test_results:
            if not result['success']:
                print(f"   ❌ {result['test']}: {result['details']}")
        sys.exit(1)

def login():
    """Login and get token"""
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def test_timestamp_scenarios():
    """Test the specific scenarios from review request"""
    token = login()
    if not token:
        print("❌ Login failed")
        return
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("🕒 TIMESTAMP FIX VERIFICATION - Review Request Scenarios")
    print("=" * 60)
    
    # Scenario 1: Import new nodes via POST /api/nodes/import
    print("\n1. Testing import new nodes via POST /api/nodes/import")
    timestamp = str(int(time.time()))
    import_data = {
        "data": f"testuser{timestamp}:testpass@10.10.10.{timestamp[-2:]}:1723",
        "protocol": "pptp",
        "testing_mode": "no_test"
    }
    
    before_import = datetime.now()
    response = requests.post(f"{API_URL}/nodes/import", json=import_data, headers=headers)
    after_import = datetime.now()
    
    if response.status_code == 200:
        result = response.json()
        if result.get('report', {}).get('added', 0) > 0:
            print(f"✅ Import successful: {result['report']['added']} nodes added")
            
            # Get the imported node
            ip = f"10.10.10.{timestamp[-2:]}"
            response = requests.get(f"{API_URL}/nodes?ip={ip}", headers=headers)
            if response.status_code == 200:
                nodes = response.json()['nodes']
                if nodes:
                    node = nodes[0]
                    last_update_str = node.get('last_update')
                    if last_update_str:
                        try:
                            last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                            time_diff = abs((after_import - last_update).total_seconds())
                            
                            if time_diff <= 120:  # Within 2 minutes
                                print(f"✅ IMPORT TIMESTAMP CORRECT: {last_update_str} (diff: {time_diff:.1f}s)")
                            else:
                                print(f"❌ IMPORT TIMESTAMP TOO OLD: {last_update_str} (diff: {time_diff:.1f}s)")
                        except Exception as e:
                            print(f"❌ TIMESTAMP PARSE ERROR: {e}")
                    else:
                        print("❌ NO TIMESTAMP IN RESPONSE")
                else:
                    print("❌ IMPORTED NODE NOT FOUND")
            else:
                print(f"❌ Failed to get imported node: {response.status_code}")
        else:
            print(f"❌ No nodes added: {result}")
    else:
        print(f"❌ Import failed: {response.status_code} - {response.text}")
    
    # Scenario 2: Create single node via POST /api/nodes
    print("\n2. Testing create single node via POST /api/nodes")
    timestamp = str(int(time.time()))
    node_data = {
        "ip": f"11.11.11.{timestamp[-2:]}",
        "login": "test",
        "password": "test123",
        "protocol": "pptp"
    }
    
    before_create = datetime.now()
    response = requests.post(f"{API_URL}/nodes", json=node_data, headers=headers)
    after_create = datetime.now()
    
    if response.status_code == 200:
        node = response.json()
        last_update_str = node.get('last_update')
        if last_update_str:
            try:
                last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                time_diff = abs((after_create - last_update).total_seconds())
                
                if time_diff <= 60:  # Within 1 minute
                    print(f"✅ CREATE TIMESTAMP CORRECT: {last_update_str} (diff: {time_diff:.1f}s)")
                else:
                    print(f"❌ CREATE TIMESTAMP TOO OLD: {last_update_str} (diff: {time_diff:.1f}s)")
            except Exception as e:
                print(f"❌ TIMESTAMP PARSE ERROR: {e}")
        else:
            print("❌ NO TIMESTAMP IN RESPONSE")
    else:
        print(f"❌ Create failed: {response.status_code} - {response.text}")
    
    # Scenario 3: Query nodes via GET /api/nodes
    print("\n3. Testing query nodes via GET /api/nodes")
    response = requests.get(f"{API_URL}/nodes?limit=10", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        nodes = result.get('nodes', [])
        if nodes:
            print(f"✅ Retrieved {len(nodes)} nodes")
            
            # Check timestamps of first few nodes
            recent_nodes = 0
            old_nodes = 0
            now = datetime.now()
            
            for i, node in enumerate(nodes[:5]):  # Check first 5 nodes
                last_update_str = node.get('last_update')
                if last_update_str:
                    try:
                        last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                        time_diff = abs((now - last_update).total_seconds())
                        
                        if time_diff <= 3600:  # Within 1 hour
                            recent_nodes += 1
                            print(f"  Node {node['id']}: ✅ Recent ({time_diff/60:.1f} min ago)")
                        else:
                            old_nodes += 1
                            print(f"  Node {node['id']}: ⏰ Old ({time_diff/3600:.1f} hours ago)")
                    except Exception as e:
                        print(f"  Node {node['id']}: ❌ Parse error: {e}")
                else:
                    print(f"  Node {node['id']}: ❌ No timestamp")
            
            print(f"Summary: {recent_nodes} recent nodes, {old_nodes} old nodes")
        else:
            print("❌ NO NODES FOUND")
    else:
        print(f"❌ Query failed: {response.status_code} - {response.text}")
    
    print("\n" + "=" * 60)
    print("TIMESTAMP FIX VERIFICATION COMPLETE")

if __name__ == "__main__":
    test_timestamp_scenarios()