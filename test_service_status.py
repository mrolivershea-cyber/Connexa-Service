#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime

class ServiceStatusTester:
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

    def test_service_status_preservation(self):
        """CRITICAL TEST: Service Status Preservation - speed_ok nodes should remain speed_ok on service failure"""
        print("\n🔥 CRITICAL SERVICE STATUS PRESERVATION TEST")
        print("=" * 60)
        
        # Step 1: Get or create speed_ok nodes for testing
        success, response = self.make_request('GET', 'nodes?status=speed_ok&limit=5')
        
        speed_ok_nodes = []
        if success and 'nodes' in response and response['nodes']:
            speed_ok_nodes = response['nodes'][:2]  # Use first 2 nodes
            print(f"📋 Found {len(speed_ok_nodes)} existing speed_ok nodes")
        else:
            # Create test nodes with speed_ok status if none exist
            print("📋 No speed_ok nodes found, creating test nodes...")
            
            # Create test nodes
            test_nodes_data = [
                {
                    "ip": "192.168.100.1",
                    "login": "testuser1",
                    "password": "testpass1",
                    "protocol": "pptp",
                    "provider": "TestProvider1",
                    "country": "United States",
                    "state": "California"
                },
                {
                    "ip": "192.168.100.2", 
                    "login": "testuser2",
                    "password": "testpass2",
                    "protocol": "pptp",
                    "provider": "TestProvider2",
                    "country": "United States",
                    "state": "Texas"
                }
            ]
            
            for node_data in test_nodes_data:
                create_success, create_response = self.make_request('POST', 'nodes', node_data)
                if create_success and 'id' in create_response:
                    # Manually set status to speed_ok via update
                    update_data = {"status": "speed_ok"}
                    self.make_request('PUT', f'nodes/{create_response["id"]}', update_data)
                    speed_ok_nodes.append(create_response)
        
        if len(speed_ok_nodes) < 2:
            print(f"❌ Could not get/create enough speed_ok nodes. Found: {len(speed_ok_nodes)}")
            return False
        
        node_ids = [node['id'] for node in speed_ok_nodes]
        print(f"📋 Testing with nodes: {node_ids}")
        
        # Step 2: Get initial speed_ok count
        initial_stats_success, initial_stats = self.make_request('GET', 'stats')
        initial_speed_ok_count = initial_stats.get('speed_ok', 0) if initial_stats_success else 0
        print(f"📊 Initial speed_ok count: {initial_speed_ok_count}")
        
        # Step 3: Test /api/services/start endpoint
        print(f"\n🚀 TESTING /api/services/start")
        service_data = {"node_ids": node_ids, "action": "start"}
        service_success, service_response = self.make_request('POST', 'services/start', service_data)
        
        if not service_success or 'results' not in service_response:
            print(f"❌ Service start API failed: {service_response}")
            return False
        
        # Check API response messages
        api_preservation_working = True
        for result in service_response['results']:
            node_id = result['node_id']
            message = result.get('message', '')
            status = result.get('status', '')
            
            print(f"   Node {node_id}: {message} (Status: {status})")
            
            # Check if API response indicates status preservation
            if 'status remains speed_ok' not in message and status != 'speed_ok':
                api_preservation_working = False
        
        # Step 4: Verify database persistence
        print(f"\n🔍 VERIFYING DATABASE PERSISTENCE")
        database_preservation_working = True
        
        for node_id in node_ids:
            node_success, node_response = self.make_request('GET', f'nodes?id={node_id}')
            if node_success and 'nodes' in node_response and node_response['nodes']:
                node = node_response['nodes'][0]
                actual_status = node.get('status', '')
                print(f"   Node {node_id}: Database status = {actual_status}")
                
                if actual_status != 'speed_ok':
                    database_preservation_working = False
                    print(f"   ❌ Node {node_id} was downgraded from speed_ok to {actual_status}")
            else:
                database_preservation_working = False
                print(f"   ❌ Could not retrieve node {node_id}")
        
        # Step 5: Test /api/manual/launch-services endpoint
        print(f"\n🚀 TESTING /api/manual/launch-services")
        manual_data = {"node_ids": node_ids}
        manual_success, manual_response = self.make_request('POST', 'manual/launch-services', manual_data)
        
        manual_api_preservation_working = True
        manual_database_preservation_working = True
        
        if manual_success and 'results' in manual_response:
            # Check API response messages
            for result in manual_response['results']:
                node_id = result['node_id']
                message = result.get('message', '')
                status = result.get('status', '')
                
                print(f"   Node {node_id}: {message} (Status: {status})")
                
                # Check if API response indicates status preservation
                if 'remains speed_ok' not in message and status != 'speed_ok':
                    manual_api_preservation_working = False
            
            # Verify database persistence again
            print(f"\n🔍 VERIFYING DATABASE PERSISTENCE AFTER MANUAL LAUNCH")
            for node_id in node_ids:
                node_success, node_response = self.make_request('GET', f'nodes?id={node_id}')
                if node_success and 'nodes' in node_response and node_response['nodes']:
                    node = node_response['nodes'][0]
                    actual_status = node.get('status', '')
                    print(f"   Node {node_id}: Database status = {actual_status}")
                    
                    if actual_status != 'speed_ok':
                        manual_database_preservation_working = False
                        print(f"   ❌ Node {node_id} was downgraded from speed_ok to {actual_status}")
                else:
                    manual_database_preservation_working = False
                    print(f"   ❌ Could not retrieve node {node_id}")
        
        # Step 6: Check final speed_ok count
        final_stats_success, final_stats = self.make_request('GET', 'stats')
        final_speed_ok_count = final_stats.get('speed_ok', 0) if final_stats_success else 0
        print(f"📊 Final speed_ok count: {final_speed_ok_count}")
        
        count_preserved = final_speed_ok_count >= initial_speed_ok_count
        
        # Step 7: Overall assessment
        print(f"\n📋 CRITICAL TEST RESULTS:")
        print(f"   ✅ /api/services/start API responses: {'WORKING' if api_preservation_working else 'FAILED'}")
        print(f"   ✅ /api/services/start DB persistence: {'WORKING' if database_preservation_working else 'FAILED'}")
        print(f"   ✅ /api/manual/launch-services API responses: {'WORKING' if manual_api_preservation_working else 'FAILED'}")
        print(f"   ✅ /api/manual/launch-services DB persistence: {'WORKING' if manual_database_preservation_working else 'FAILED'}")
        print(f"   ✅ Speed_ok count preserved: {'WORKING' if count_preserved else 'FAILED'}")
        
        overall_success = (api_preservation_working and database_preservation_working and 
                          manual_api_preservation_working and manual_database_preservation_working and 
                          count_preserved)
        
        if overall_success:
            print("\n✅ CRITICAL TEST PASSED: Service status preservation working correctly")
            return True
        else:
            failure_details = []
            if not api_preservation_working:
                failure_details.append("/api/services/start API responses incorrect")
            if not database_preservation_working:
                failure_details.append("/api/services/start database persistence failed")
            if not manual_api_preservation_working:
                failure_details.append("/api/manual/launch-services API responses incorrect")
            if not manual_database_preservation_working:
                failure_details.append("/api/manual/launch-services database persistence failed")
            if not count_preserved:
                failure_details.append(f"speed_ok count decreased from {initial_speed_ok_count} to {final_speed_ok_count}")
            
            print(f"\n❌ CRITICAL TEST FAILED: {'; '.join(failure_details)}")
            return False

def main():
    tester = ServiceStatusTester()
    
    if not tester.login():
        sys.exit(1)
    
    success = tester.test_service_status_preservation()
    
    if success:
        print("\n🎉 SERVICE STATUS PRESERVATION TEST COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        print("\n💥 SERVICE STATUS PRESERVATION TEST FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()