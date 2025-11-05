#!/usr/bin/env python3

import requests
import sys

class DeduplicationDebugger:
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
            return True
        return False

    def clear_test_data(self):
        """Clear any existing test data"""
        # Delete nodes with test IP
        response = requests.get(f"{self.api_url}/nodes", 
                              headers=self.headers, 
                              params={'ip': '192.168.99.99', 'limit': 100})
        
        if response.status_code == 200:
            data = response.json()
            nodes = data.get('nodes', [])
            
            if nodes:
                node_ids = [node['id'] for node in nodes]
                delete_response = requests.delete(f"{self.api_url}/nodes", 
                                                headers=self.headers, 
                                                json={'node_ids': node_ids})
                print(f"🧹 Cleared {len(node_ids)} existing test nodes")

    def test_simple_duplicate(self):
        """Test simple duplicate detection"""
        print("\n🧪 TEST: Simple duplicate detection")
        
        # First import
        data1 = """Ip: 192.168.99.99
Login: testuser
Pass: testpass
State: CA"""

        import_data = {"data": data1, "protocol": "pptp"}
        response1 = requests.post(f"{self.api_url}/nodes/import", 
                                headers=self.headers, json=import_data)
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"   First import: {result1.get('report', {}).get('added', 0)} added")
        
        # Second import (same data)
        response2 = requests.post(f"{self.api_url}/nodes/import", 
                                headers=self.headers, json=import_data)
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"   Second import: {result2.get('report', {}).get('added', 0)} added, {result2.get('report', {}).get('skipped_duplicates', 0)} skipped")
            
            # Check database
            check_response = requests.get(f"{self.api_url}/nodes", 
                                        headers=self.headers, 
                                        params={'ip': '192.168.99.99'})
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                count = len(check_data.get('nodes', []))
                print(f"   Database count: {count} (should be 1)")
                
                if count == 1:
                    print("   ✅ Simple duplicate detection working")
                    return True
                else:
                    print("   ❌ Simple duplicate detection failed")
                    return False
        
        return False

    def test_within_import_duplicates(self):
        """Test within-import duplicate detection"""
        print("\n🧪 TEST: Within-import duplicate detection")
        
        # Clear test data first
        self.clear_test_data()
        
        # Import with duplicates within the same request
        data_with_duplicates = """Ip: 192.168.99.99
Login: testuser
Pass: testpass
State: CA

Ip: 192.168.99.100
Login: testuser2
Pass: testpass2
State: NY

Ip: 192.168.99.99
Login: testuser
Pass: testpass
State: CA"""

        import_data = {"data": data_with_duplicates, "protocol": "pptp"}
        response = requests.post(f"{self.api_url}/nodes/import", 
                               headers=self.headers, json=import_data)
        
        if response.status_code == 200:
            result = response.json()
            report = result.get('report', {})
            
            print(f"   Processed: {report.get('total_processed', 0)}")
            print(f"   Added: {report.get('added', 0)}")
            print(f"   Skipped: {report.get('skipped_duplicates', 0)}")
            
            # Check database
            check_response = requests.get(f"{self.api_url}/nodes", 
                                        headers=self.headers, 
                                        params={'ip': '192.168.99.99'})
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                count = len(check_data.get('nodes', []))
                print(f"   Database count for 192.168.99.99: {count} (should be 1)")
                
                if (report.get('total_processed', 0) == 3 and 
                    report.get('added', 0) == 2 and 
                    report.get('skipped_duplicates', 0) == 1 and 
                    count == 1):
                    print("   ✅ Within-import duplicate detection working")
                    return True
                else:
                    print("   ❌ Within-import duplicate detection failed")
                    return False
        
        return False

    def test_batch_processing_issue(self):
        """Test if batch processing causes duplicate issues"""
        print("\n🧪 TEST: Batch processing duplicate issue")
        
        # Clear test data
        self.clear_test_data()
        
        # Create a batch with the same IP appearing multiple times
        batch_data = ""
        for i in range(10):
            batch_data += f"""Ip: 192.168.99.99
Login: testuser
Pass: testpass
State: CA
City: TestCity{i}

"""
        
        import_data = {"data": batch_data, "protocol": "pptp"}
        response = requests.post(f"{self.api_url}/nodes/import", 
                               headers=self.headers, json=import_data)
        
        if response.status_code == 200:
            result = response.json()
            report = result.get('report', {})
            
            print(f"   Processed: {report.get('total_processed', 0)}")
            print(f"   Added: {report.get('added', 0)}")
            print(f"   Skipped: {report.get('skipped_duplicates', 0)}")
            
            # Check database
            check_response = requests.get(f"{self.api_url}/nodes", 
                                        headers=self.headers, 
                                        params={'ip': '192.168.99.99'})
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                count = len(check_data.get('nodes', []))
                print(f"   Database count: {count} (should be 1)")
                
                if count == 1:
                    print("   ✅ Batch processing duplicate detection working")
                    return True
                else:
                    print("   ❌ Batch processing duplicate detection failed")
                    # Show details of duplicates
                    for node in check_data.get('nodes', [])[:5]:
                        print(f"     - ID: {node.get('id')}, City: {node.get('city')}, Last Update: {node.get('last_update')}")
                    return False
        
        return False

    def run_debug_tests(self):
        """Run all debug tests"""
        print("🔬 DEDUPLICATION DEBUG TESTS")
        print("=" * 40)
        
        if not self.login():
            print("❌ Login failed")
            return False
        
        test1 = self.test_simple_duplicate()
        test2 = self.test_within_import_duplicates()
        test3 = self.test_batch_processing_issue()
        
        print("\n" + "=" * 40)
        print("🏁 DEBUG TEST SUMMARY:")
        print(f"   Simple duplicate: {'✅ PASSED' if test1 else '❌ FAILED'}")
        print(f"   Within-import: {'✅ PASSED' if test2 else '❌ FAILED'}")
        print(f"   Batch processing: {'✅ PASSED' if test3 else '❌ FAILED'}")
        
        overall = test1 and test2 and test3
        print(f"   OVERALL: {'✅ ALL TESTS PASSED' if overall else '❌ SOME TESTS FAILED'}")
        
        if not overall:
            print("\n🚨 CRITICAL ISSUE CONFIRMED:")
            print("   The deduplication system has bugs that allow duplicates")
            print("   to be added to the database, especially in batch processing.")
        
        return overall

if __name__ == "__main__":
    debugger = DeduplicationDebugger()
    success = debugger.run_debug_tests()
    sys.exit(0 if success else 1)