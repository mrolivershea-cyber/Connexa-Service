#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class FinalVerificationTester:
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

    def test_login(self):
        """Login with admin credentials"""
        login_data = {"username": "admin", "password": "admin"}
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def run_final_verification(self):
        """Run final comprehensive verification of all requirements"""
        print("🎯 FINAL VERIFICATION OF SIMPLIFIED IMPORT REQUIREMENTS")
        print("=" * 80)
        print("Testing all requirements from the Russian user review request:")
        print("1. Always uses testing_mode='no_test' regardless of input")
        print("2. Returns session_id=None (no testing sessions)")
        print("3. Assigns status 'not_tested' to all new nodes")
        print("4. No automatic testing triggered")
        print("5. Manual testing endpoints still work")
        print("=" * 80)
        
        if not self.test_login():
            print("❌ Cannot proceed without login")
            return False
        
        # REQUIREMENT 1: Always uses testing_mode="no_test"
        print("\n📋 REQUIREMENT 1: Always uses testing_mode='no_test'")
        print("-" * 60)
        
        test_inputs = [
            {"testing_mode": "ping_only", "desc": "ping_only input"},
            {"testing_mode": "speed_only", "desc": "speed_only input"},
            {"testing_mode": "both", "desc": "both input"},
            {"desc": "no testing_mode field"}
        ]
        
        req1_passed = True
        for i, test_input in enumerate(test_inputs, 1):
            import_data = {
                "data": f"192.168.250.{i} req1test{i} testpass{i} CA",
                "protocol": "pptp"
            }
            
            if "testing_mode" in test_input:
                import_data["testing_mode"] = test_input["testing_mode"]
            
            success, response = self.make_request('POST', 'nodes/import', import_data)
            
            if success and 'report' in response:
                testing_mode = response['report'].get('testing_mode')
                if testing_mode == 'no_test':
                    print(f"   ✅ Test {i} ({test_input['desc']}): testing_mode = '{testing_mode}'")
                else:
                    print(f"   ❌ Test {i} ({test_input['desc']}): testing_mode = '{testing_mode}' (should be 'no_test')")
                    req1_passed = False
            else:
                print(f"   ❌ Test {i} failed: {response}")
                req1_passed = False
        
        print(f"REQUIREMENT 1: {'✅ PASSED' if req1_passed else '❌ FAILED'}")
        
        # REQUIREMENT 2: Returns session_id=None
        print("\n📋 REQUIREMENT 2: Returns session_id=None")
        print("-" * 60)
        
        import_data = {
            "data": "192.168.251.1 req2test testpass CA",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        req2_passed = False
        
        if success:
            session_id = response.get('session_id')
            if session_id is None:
                print(f"   ✅ session_id = {session_id} (correct)")
                req2_passed = True
            else:
                print(f"   ❌ session_id = {session_id} (should be None)")
        else:
            print(f"   ❌ Import failed: {response}")
        
        print(f"REQUIREMENT 2: {'✅ PASSED' if req2_passed else '❌ FAILED'}")
        
        # REQUIREMENT 3: Assigns status "not_tested" to all new nodes
        print("\n📋 REQUIREMENT 3: Assigns status 'not_tested' to all new nodes")
        print("-" * 60)
        
        import_data = {
            "data": """192.168.252.1 req3test1 testpass1 CA
192.168.252.2 req3test2 testpass2 TX
192.168.252.3 req3test3 testpass3 FL""",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        req3_passed = True
        
        if success and 'report' in response:
            added = response['report'].get('added', 0)
            if added >= 3:
                # Check each node's status
                for i in range(1, 4):
                    ip = f"192.168.252.{i}"
                    nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                    
                    if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                        node = nodes_response['nodes'][0]
                        status = node.get('status')
                        if status == 'not_tested':
                            print(f"   ✅ Node {ip}: status = '{status}'")
                        else:
                            print(f"   ❌ Node {ip}: status = '{status}' (should be 'not_tested')")
                            req3_passed = False
                    else:
                        print(f"   ❌ Node {ip}: not found")
                        req3_passed = False
            else:
                print(f"   ❌ Only {added} nodes added, expected 3")
                req3_passed = False
        else:
            print(f"   ❌ Import failed: {response}")
            req3_passed = False
        
        print(f"REQUIREMENT 3: {'✅ PASSED' if req3_passed else '❌ FAILED'}")
        
        # REQUIREMENT 4: No automatic testing triggered
        print("\n📋 REQUIREMENT 4: No automatic testing triggered")
        print("-" * 60)
        
        import_data = {
            "data": """192.168.253.1 req4test1 testpass1 CA
192.168.253.2 req4test2 testpass2 TX""",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        req4_passed = True
        
        if success:
            print("   Import completed, waiting 15 seconds to check for automatic testing...")
            time.sleep(15)
            
            # Check if nodes are still 'not_tested'
            for i in range(1, 3):
                ip = f"192.168.253.{i}"
                nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
                
                if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                    node = nodes_response['nodes'][0]
                    status = node.get('status')
                    if status == 'not_tested':
                        print(f"   ✅ Node {ip}: still 'not_tested' (no automatic testing)")
                    else:
                        print(f"   ❌ Node {ip}: status changed to '{status}' (automatic testing detected!)")
                        req4_passed = False
                else:
                    print(f"   ❌ Node {ip}: not found")
                    req4_passed = False
        else:
            print(f"   ❌ Import failed: {response}")
            req4_passed = False
        
        print(f"REQUIREMENT 4: {'✅ PASSED' if req4_passed else '❌ FAILED'}")
        
        # REQUIREMENT 5: Manual testing endpoints still work
        print("\n📋 REQUIREMENT 5: Manual testing endpoints still work")
        print("-" * 60)
        
        # Create a test node first
        import_data = {
            "data": "192.168.254.1 req5test testpass CA",
            "protocol": "pptp"
        }
        
        success, response = self.make_request('POST', 'nodes/import', import_data)
        req5_passed = False
        
        if success:
            # Get the node ID
            nodes_success, nodes_response = self.make_request('GET', 'nodes?ip=192.168.254.1')
            
            if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                node_id = nodes_response['nodes'][0]['id']
                
                # Test manual ping endpoint
                ping_data = {"node_ids": [node_id]}
                ping_success, ping_response = self.make_request('POST', 'manual/ping-test', ping_data)
                
                if ping_success and 'results' in ping_response:
                    print("   ✅ Manual ping test endpoint working")
                    
                    # Test manual speed endpoint (might fail due to status, but should be accessible)
                    speed_data = {"node_ids": [node_id]}
                    speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
                    
                    # Speed test might return 400 due to status requirements, but endpoint should be accessible
                    if speed_success or speed_response.get('status_code') in [400, 422]:
                        print("   ✅ Manual speed test endpoint accessible")
                        
                        # Test manual launch services endpoint
                        launch_data = {"node_ids": [node_id]}
                        launch_success, launch_response = self.make_request('POST', 'manual/launch-services', launch_data)
                        
                        if launch_success or launch_response.get('status_code') in [400, 422]:
                            print("   ✅ Manual launch services endpoint accessible")
                            req5_passed = True
                        else:
                            print(f"   ❌ Launch services endpoint failed: {launch_response}")
                    else:
                        print(f"   ❌ Speed test endpoint failed: {speed_response}")
                else:
                    print(f"   ❌ Ping test endpoint failed: {ping_response}")
            else:
                print("   ❌ Could not retrieve test node")
        else:
            print(f"   ❌ Could not create test node: {response}")
        
        print(f"REQUIREMENT 5: {'✅ PASSED' if req5_passed else '❌ FAILED'}")
        
        # FINAL SUMMARY
        print("\n" + "=" * 80)
        print("🏁 FINAL VERIFICATION SUMMARY")
        print("=" * 80)
        
        all_requirements = [req1_passed, req2_passed, req3_passed, req4_passed, req5_passed]
        passed_count = sum(all_requirements)
        
        print(f"Requirements passed: {passed_count}/5")
        print(f"Success rate: {passed_count/5*100:.1f}%")
        
        print("\nDetailed results:")
        print(f"1. Always uses testing_mode='no_test': {'✅ PASSED' if req1_passed else '❌ FAILED'}")
        print(f"2. Returns session_id=None: {'✅ PASSED' if req2_passed else '❌ FAILED'}")
        print(f"3. Assigns 'not_tested' status: {'✅ PASSED' if req3_passed else '❌ FAILED'}")
        print(f"4. No automatic testing: {'✅ PASSED' if req4_passed else '❌ FAILED'}")
        print(f"5. Manual testing works: {'✅ PASSED' if req5_passed else '❌ FAILED'}")
        
        if passed_count == 5:
            print("\n🎉 ALL REQUIREMENTS SATISFIED!")
            print("✅ Simplified import process is working correctly")
            print("✅ Ready for production use")
        else:
            print(f"\n⚠️  {5-passed_count} REQUIREMENTS NOT MET")
            print("❌ Issues need to be addressed")
        
        return passed_count == 5

if __name__ == "__main__":
    tester = FinalVerificationTester()
    success = tester.run_final_verification()
    sys.exit(0 if success else 1)