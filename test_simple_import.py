#!/usr/bin/env python3

import requests
import json
import time

# Test the import functionality
base_url = "https://memory-mcp.preview.emergentagent.com"
api_url = f"{base_url}/api"

# Login
login_data = {"username": "admin", "password": "admin"}
response = requests.post(f"{api_url}/auth/login", json=login_data)
token = response.json()['access_token']
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}

print("🇷🇺 TESTING RESTORED IMPORT FUNCTIONALITY")
print("=" * 50)

# Test 1: Import with duplicates
print("\n📝 Test 1: Import with duplicates")

# First import
initial_data = {
    "data": "5.78.150.1:testuser1:testpass1\n5.78.150.2:testuser2:testpass2",
    "protocol": "pptp"
}

response1 = requests.post(f"{api_url}/nodes/import", json=initial_data, headers=headers)
print(f"First import: {response1.status_code}")
if response1.status_code == 200:
    report1 = response1.json().get('report', {})
    print(f"  Added: {report1.get('added', 0)}, Skipped: {report1.get('skipped_duplicates', 0)}")

# Second import with duplicates
duplicate_data = {
    "data": "5.78.150.1:testuser1:testpass1\n5.78.150.3:testuser3:testpass3",
    "protocol": "pptp"
}

response2 = requests.post(f"{api_url}/nodes/import", json=duplicate_data, headers=headers)
print(f"Second import: {response2.status_code}")
if response2.status_code == 200:
    report2 = response2.json().get('report', {})
    print(f"  Added: {report2.get('added', 0)}, Skipped: {report2.get('skipped_duplicates', 0)}")
    
    if report2.get('added', 0) >= 1 and report2.get('skipped_duplicates', 0) >= 1:
        print("✅ Duplicate detection working!")
    else:
        print("❌ Duplicate detection not working as expected")

# Test 2: Chunked import with final report
print("\n📝 Test 2: Chunked import final report")

# Create larger data for chunked import
large_data_lines = []
for i in range(2000):
    large_data_lines.append(f"10.10.{(i//256)+1}.{i%256}:bulkuser{i}:bulkpass{i}")

large_data = {
    "data": "\n".join(large_data_lines),
    "protocol": "pptp"
}

response3 = requests.post(f"{api_url}/nodes/import-chunked", json=large_data, headers=headers)
print(f"Chunked import start: {response3.status_code}")

if response3.status_code == 200:
    session_id = response3.json().get('session_id')
    print(f"Session ID: {session_id}")
    
    # Wait for completion
    for i in range(30):  # Wait up to 60 seconds
        progress_response = requests.get(f"{api_url}/import/progress/{session_id}", headers=headers)
        if progress_response.status_code == 200:
            progress = progress_response.json()
            status = progress.get('status', 'unknown')
            print(f"  Status: {status}")
            
            if status == 'completed':
                final_report = progress.get('final_report', {})
                if final_report:
                    print(f"✅ Final report found!")
                    print(f"  Added: {final_report.get('added', 0)}")
                    print(f"  Success rate: {final_report.get('success_rate', 0)}%")
                    break
                else:
                    print("❌ No final report found")
                    break
            elif status == 'failed':
                print(f"❌ Import failed: {progress.get('current_operation', 'unknown')}")
                break
        
        time.sleep(2)

# Test 3: Bulk deletion (using correct endpoint)
print("\n📝 Test 3: Bulk deletion")

# Create test nodes
test_data = {
    "data": "10.0.250.1:deltest1:delpass1\n10.0.250.2:deltest2:delpass2",
    "protocol": "pptp"
}

response4 = requests.post(f"{api_url}/nodes/import", json=test_data, headers=headers)
print(f"Test nodes created: {response4.status_code}")

# Try bulk delete with query parameters
bulk_delete_url = f"{api_url}/nodes/bulk?search=deltest"
response5 = requests.delete(bulk_delete_url, headers=headers)
print(f"Bulk delete: {response5.status_code}")

if response5.status_code == 200:
    result = response5.json()
    deleted_count = result.get('deleted_count', 0)
    print(f"✅ Bulk delete working: {deleted_count} nodes deleted")
else:
    print(f"❌ Bulk delete failed: {response5.text}")

print("\n" + "=" * 50)
print("🏁 TESTING COMPLETE")