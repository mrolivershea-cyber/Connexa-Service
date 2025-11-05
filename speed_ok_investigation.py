#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class SpeedOKInvestigator:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

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
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response}")
            return False

    def investigate_speed_ok_false_positives(self):
        """CRITICAL: Investigate false SPEED_OK results reported by Russian user"""
        print("\n🔥 CRITICAL INVESTIGATION: SPEED_OK False Positives")
        print("User reports: 9 speed_ok configs don't work when manually connecting")
        
        # Test the specific IPs mentioned in the review request
        test_ips = [
            {"ip": "5.78.73.148", "login": "admin", "password": "admin", "claimed_speed": 1.3},
            {"ip": "5.78.66.53", "login": "admin", "password": "admin", "claimed_speed": 1.3},
            {"ip": "5.78.59.111", "login": "admin", "password": "admin", "claimed_speed": 1.3},
            {"ip": "5.78.107.168", "login": "admin", "password": "admin", "claimed_speed": 1.3},
            {"ip": "5.78.51.215", "login": "admin", "password": "admin", "claimed_speed": 0.1}
        ]
        
        investigation_results = []
        
        for test_case in test_ips:
            ip = test_case["ip"]
            login = test_case["login"]
            password = test_case["password"]
            claimed_speed = test_case["claimed_speed"]
            
            print(f"\n🔍 Testing {ip} (claimed {claimed_speed} Mbps)...")
            
            result = {
                "ip": ip,
                "claimed_speed": claimed_speed,
                "ping_light_test": None,
                "ping_ok_test": None,
                "database_status": None,
                "speed_test": None,
                "verdict": None
            }
            
            # 1. PING LIGHT TEST - TCP port 1723 connectivity
            # First get the node ID for this IP
            nodes_success_temp, nodes_response_temp = self.make_request('GET', f'nodes?ip={ip}')
            if nodes_success_temp and 'nodes' in nodes_response_temp and nodes_response_temp['nodes']:
                node_id_temp = nodes_response_temp['nodes'][0]['id']
                ping_light_data = {"node_ids": [node_id_temp]}
                ping_light_success, ping_light_response = self.make_request('POST', 'manual/ping-light-test', ping_light_data)
            else:
                ping_light_success, ping_light_response = False, {"error": "Node not found for ping light test"}
            
            if ping_light_success and 'results' in ping_light_response:
                ping_light_result = ping_light_response['results'][0] if ping_light_response['results'] else {}
                result["ping_light_test"] = {
                    "success": ping_light_result.get("success", False),
                    "message": ping_light_result.get("message", ""),
                    "response_time": ping_light_result.get("response_time", 0)
                }
                print(f"  📡 PING LIGHT: {'✅ PASS' if ping_light_result.get('success') else '❌ FAIL'} - {ping_light_result.get('message', '')}")
            else:
                result["ping_light_test"] = {"success": False, "message": f"API call failed: {ping_light_response}"}
                print(f"  📡 PING LIGHT: ❌ API FAILED - {ping_light_response}")
            
            # 2. Check database status
            nodes_success, nodes_response = self.make_request('GET', f'nodes?ip={ip}')
            if nodes_success and 'nodes' in nodes_response and nodes_response['nodes']:
                node = nodes_response['nodes'][0]
                result["database_status"] = {
                    "status": node.get("status"),
                    "login": node.get("login"),
                    "password": node.get("password"),
                    "last_update": node.get("last_update")
                }
                print(f"  💾 DATABASE: Status={node.get('status')}, Login={node.get('login')}, Pass={node.get('password')}")
            else:
                result["database_status"] = {"status": "not_found"}
                print(f"  💾 DATABASE: ❌ NODE NOT FOUND")
            
            # 3. PING OK TEST - Full PPTP authentication
            if result["database_status"]["status"] != "not_found":
                node_id = nodes_response['nodes'][0]['id']
                
                # First, reset the node to not_tested to force a real ping test
                print(f"    🔄 Resetting node {node_id} to not_tested status to force real ping test...")
                reset_success, reset_response = self.make_request('PUT', f'nodes/{node_id}', {"status": "not_tested"})
                if reset_success:
                    print(f"    ✅ Node reset to not_tested")
                else:
                    print(f"    ❌ Failed to reset node: {reset_response}")
                
                ping_ok_data = {"node_ids": [node_id]}
                ping_ok_success, ping_ok_response = self.make_request('POST', 'manual/ping-test', ping_ok_data)
                
                if ping_ok_success and 'results' in ping_ok_response:
                    ping_ok_result = ping_ok_response['results'][0] if ping_ok_response['results'] else {}
                    result["ping_ok_test"] = {
                        "success": ping_ok_result.get("success", False),
                        "message": ping_ok_result.get("message", ""),
                        "new_status": ping_ok_result.get("new_status", "")
                    }
                    print(f"  🔐 PING OK: {'✅ PASS' if ping_ok_result.get('success') else '❌ FAIL'} - {ping_ok_result.get('message', '')}")
                else:
                    result["ping_ok_test"] = {"success": False, "message": f"API call failed: {ping_ok_response}"}
                    print(f"  🔐 PING OK: ❌ API FAILED - {ping_ok_response}")
                
                # 4. SPEED TEST (if ping_ok passes)
                if result["ping_ok_test"] and result["ping_ok_test"]["success"]:
                    speed_data = {"node_ids": [node_id]}
                    speed_success, speed_response = self.make_request('POST', 'manual/speed-test', speed_data)
                    
                    if speed_success and 'results' in speed_response:
                        speed_result = speed_response['results'][0] if speed_response['results'] else {}
                        result["speed_test"] = {
                            "success": speed_result.get("success", False),
                            "message": speed_result.get("message", ""),
                            "download": speed_result.get("download", 0),
                            "upload": speed_result.get("upload", 0)
                        }
                        print(f"  🚀 SPEED TEST: {'✅ PASS' if speed_result.get('success') else '❌ FAIL'} - {speed_result.get('message', '')}")
                        if speed_result.get("success"):
                            download = speed_result.get('download', 0)
                            upload = speed_result.get('upload', 0)
                            print(f"    📊 Speed: {download} Mbps down, {upload} Mbps up")
                            # CRITICAL: Check if speeds are suspiciously zero
                            if download == 0 and upload == 0:
                                print(f"    🚨 CRITICAL: Zero speeds detected - possible fake speed test result!")
                        else:
                            print(f"    🚨 Speed test failed: {speed_result}")
                        
                        # Print full speed test response for debugging
                        print(f"    🔍 Full speed response: {speed_response}")
                    else:
                        result["speed_test"] = {"success": False, "message": f"API call failed: {speed_response}"}
                        print(f"  🚀 SPEED TEST: ❌ API FAILED - {speed_response}")
            
            # 5. VERDICT
            ping_light_ok = result["ping_light_test"]["success"] if result["ping_light_test"] else False
            ping_ok_ok = result["ping_ok_test"]["success"] if result["ping_ok_test"] else False
            db_status = result["database_status"]["status"] if result["database_status"] else "unknown"
            
            if db_status == "speed_ok" and not ping_ok_ok:
                result["verdict"] = "FALSE_POSITIVE - Database shows speed_ok but PPTP auth fails"
            elif db_status == "speed_ok" and ping_ok_ok:
                result["verdict"] = "NEEDS_RETESTING - PPTP works, speed test needed"
            elif db_status != "speed_ok":
                result["verdict"] = "STATUS_MISMATCH - Database status doesn't match claimed speed_ok"
            elif ping_light_ok and not ping_ok_ok:
                result["verdict"] = "AUTH_FAILURE - TCP reachable but PPTP auth fails"
            else:
                result["verdict"] = "INVESTIGATION_INCOMPLETE"
            
            print(f"  🏁 VERDICT: {result['verdict']}")
            investigation_results.append(result)
        
        # Analyze overall results
        false_positives = [r for r in investigation_results if "FALSE_POSITIVE" in r["verdict"]]
        auth_failures = [r for r in investigation_results if "AUTH_FAILURE" in r["verdict"]]
        status_mismatches = [r for r in investigation_results if "STATUS_MISMATCH" in r["verdict"]]
        
        print(f"\n📊 INVESTIGATION SUMMARY:")
        print(f"  False Positives: {len(false_positives)}")
        print(f"  Auth Failures: {len(auth_failures)}")
        print(f"  Status Mismatches: {len(status_mismatches)}")
        
        # Detailed analysis
        print(f"\n🔍 DETAILED ANALYSIS:")
        for result in investigation_results:
            print(f"  {result['ip']}: {result['verdict']}")
        
        return investigation_results

if __name__ == "__main__":
    investigator = SpeedOKInvestigator()
    
    if not investigator.login():
        sys.exit(1)
    
    results = investigator.investigate_speed_ok_false_positives()
    
    print(f"\n🏁 INVESTIGATION COMPLETE")
    print(f"Tested {len(results)} IPs from Russian user's complaint")