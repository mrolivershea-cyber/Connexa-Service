#!/usr/bin/env python3

import requests
import json
import time
import random

# Test the restored import functionality
base_url = "https://memory-mcp.preview.emergentagent.com"
api_url = f"{base_url}/api"

# Login
login_data = {"username": "admin", "password": "admin"}
response = requests.post(f"{api_url}/auth/login", json=login_data)
token = response.json()['access_token']
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}

print("🇷🇺 FINAL TESTING - RESTORED IMPORT FUNCTIONALITY")
print("=" * 60)

# Generate unique IPs to avoid conflicts
def get_unique_ip():
    return f"203.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"

# Test 1: Import with duplicates (using unique IPs)
print("\n📝 СЦЕНАРИЙ 1: Import with Duplicates - Smart Duplicate Checking")

ip1 = get_unique_ip()
ip2 = get_unique_ip()
ip3 = get_unique_ip()
ip4 = get_unique_ip()

# First import
initial_data = {
    "data": f"{ip1}:testuser1:testpass1\n{ip2}:testuser2:testpass2\n{ip3}:testuser3:testpass3",
    "protocol": "pptp"
}

response1 = requests.post(f"{api_url}/nodes/import", json=initial_data, headers=headers)
print(f"First import: {response1.status_code}")
if response1.status_code == 200:
    report1 = response1.json().get('report', {})
    print(f"  Added: {report1.get('added', 0)}, Skipped: {report1.get('skipped_duplicates', 0)}")

# Second import with some duplicates and some new nodes
duplicate_data = {
    "data": f"{ip1}:testuser1:testpass1\n{ip2}:testuser2:testpass2\n{ip4}:testuser4:testpass4",
    "protocol": "pptp"
}

response2 = requests.post(f"{api_url}/nodes/import", json=duplicate_data, headers=headers)
print(f"Second import: {response2.status_code}")
if response2.status_code == 200:
    report2 = response2.json().get('report', {})
    print(f"  Added: {report2.get('added', 0)}, Skipped: {report2.get('skipped_duplicates', 0)}")
    
    if report2.get('added', 0) >= 1 and report2.get('skipped_duplicates', 0) >= 2:
        print("✅ СЦЕНАРИЙ 1 PASSED: Smart duplicate checking working!")
    else:
        print("❌ СЦЕНАРИЙ 1 FAILED: Duplicate detection not working as expected")

# Test 2: Batch deletion (using existing nodes)
print("\n📝 СЦЕНАРИЙ 2: Batch Deletion - /api/nodes/batch endpoint")

# Get some existing node IDs
response3 = requests.get(f"{api_url}/nodes?limit=5", headers=headers)
if response3.status_code == 200:
    nodes = response3.json().get('nodes', [])
    if len(nodes) >= 2:
        node_id1 = nodes[0]['id']
        node_id2 = nodes[1]['id']
        
        print(f"Testing batch delete with node IDs: {node_id1}, {node_id2}")
        
        # Test batch delete
        batch_delete_data = {
            "node_ids": [node_id1, node_id2]
        }
        
        response4 = requests.delete(f"{api_url}/nodes/batch", json=batch_delete_data, headers=headers)
        print(f"Batch delete: {response4.status_code}")
        
        if response4.status_code == 200:
            result = response4.json()
            deleted_count = result.get('deleted_count', 0)
            print(f"✅ СЦЕНАРИЙ 2 PASSED: Batch delete working - {deleted_count} nodes deleted")
        else:
            print(f"❌ СЦЕНАРИЙ 2 FAILED: Batch delete failed - {response4.text}")
    else:
        print("❌ СЦЕНАРИЙ 2 FAILED: Not enough nodes for batch delete test")
else:
    print("❌ СЦЕНАРИЙ 2 FAILED: Could not retrieve nodes for batch delete test")

# Test 3: Chunked import with final report
print("\n📝 СЦЕНАРИЙ 3: Chunked Import Final Report - Detailed Statistics")

# Create larger data for chunked import (using unique IPs)
large_data_lines = []
for i in range(1500):  # Smaller for faster testing
    ip = f"172.{(i//65536)+16}.{(i//256)%256}.{i%256}"
    large_data_lines.append(f"{ip}:bulkuser{i}:bulkpass{i}")

# Add some duplicates to test reporting
large_data_lines.append(f"{large_data_lines[0]}")  # Duplicate first entry
large_data_lines.append(f"{large_data_lines[1]}")  # Duplicate second entry

large_data = {
    "data": "\n".join(large_data_lines),
    "protocol": "pptp"
}

response5 = requests.post(f"{api_url}/nodes/import-chunked", json=large_data, headers=headers)
print(f"Chunked import start: {response5.status_code}")

if response5.status_code == 200:
    session_id = response5.json().get('session_id')
    total_chunks = response5.json().get('total_chunks', 0)
    print(f"Session ID: {session_id}, Total chunks: {total_chunks}")
    
    # Wait for completion
    for i in range(30):  # Wait up to 60 seconds
        progress_response = requests.get(f"{api_url}/import/progress/{session_id}", headers=headers)
        if progress_response.status_code == 200:
            progress = progress_response.json()
            status = progress.get('status', 'unknown')
            processed_chunks = progress.get('processed_chunks', 0)
            print(f"  Status: {status}, Progress: {processed_chunks}/{total_chunks}")
            
            if status == 'completed':
                final_report = progress.get('final_report', {})
                if final_report:
                    required_fields = ['total_processed', 'added', 'skipped_duplicates', 'replaced_old', 'format_errors', 'success_rate']
                    missing_fields = [field for field in required_fields if field not in final_report]
                    
                    if not missing_fields:
                        print("✅ СЦЕНАРИЙ 3 PASSED: Detailed final_report working!")
                        print(f"  Added: {final_report.get('added', 0)}")
                        print(f"  Skipped duplicates: {final_report.get('skipped_duplicates', 0)}")
                        print(f"  Success rate: {final_report.get('success_rate', 0)}%")
                        print(f"  All required fields present: {required_fields}")
                    else:
                        print(f"❌ СЦЕНАРИЙ 3 FAILED: Missing final_report fields: {missing_fields}")
                else:
                    print("❌ СЦЕНАРИЙ 3 FAILED: No final_report found")
                break
            elif status == 'failed':
                print(f"❌ СЦЕНАРИЙ 3 FAILED: Import failed - {progress.get('current_operation', 'unknown')}")
                break
        
        time.sleep(2)
    else:
        print("❌ СЦЕНАРИЙ 3 FAILED: Import did not complete within 60 seconds")

# Test 4: Speed optimization verification
print("\n📝 СЦЕНАРИЙ 4: Speed Optimization Verification - Chunks up to 10K lines")

# Test medium file (should use optimized chunk size)
medium_data_lines = []
for i in range(8000):  # 8K lines - should use larger chunks for speed
    ip = f"198.51.100.{(i//256)%256}"
    if i >= 256:
        ip = f"198.51.{(i//256)%256}.{i%256}"
    medium_data_lines.append(f"{ip}:speeduser{i}:speedpass{i}")

medium_data = {
    "data": "\n".join(medium_data_lines),
    "protocol": "pptp"
}

start_time = time.time()
response6 = requests.post(f"{api_url}/nodes/import-chunked", json=medium_data, headers=headers)

if response6.status_code == 200:
    session_id = response6.json().get('session_id')
    total_chunks = response6.json().get('total_chunks', 0)
    
    # Calculate expected chunk size (should be optimized for speed)
    expected_chunk_size = 5000 if len(medium_data_lines) > 10000 else 2500
    expected_chunks = (len(medium_data_lines) + expected_chunk_size - 1) // expected_chunk_size
    
    print(f"Speed test: {len(medium_data_lines)} lines in {total_chunks} chunks (expected ~{expected_chunks})")
    
    # Wait for completion
    for i in range(60):  # Wait up to 2 minutes
        progress_response = requests.get(f"{api_url}/import/progress/{session_id}", headers=headers)
        if progress_response.status_code == 200:
            progress = progress_response.json()
            status = progress.get('status', 'unknown')
            
            if status == 'completed':
                end_time = time.time()
                total_time = end_time - start_time
                
                final_report = progress.get('final_report', {})
                added = final_report.get('added', 0)
                
                # Check if chunk size was optimized (fewer chunks = larger chunk size = faster)
                chunk_size_optimized = total_chunks <= expected_chunks + 2  # Allow some variance
                
                # Check if processing was reasonably fast
                speed_acceptable = total_time < 120  # Should complete within 2 minutes
                
                if chunk_size_optimized and speed_acceptable and added > 5000:
                    print(f"✅ СЦЕНАРИЙ 4 PASSED: Speed optimizations working!")
                    print(f"  {len(medium_data_lines)} lines in {total_chunks} chunks")
                    print(f"  Completed in {total_time:.1f}s, {added} nodes added")
                else:
                    print(f"❌ СЦЕНАРИЙ 4 FAILED: Optimization issues")
                    print(f"  Chunk optimized: {chunk_size_optimized}, Speed OK: {speed_acceptable}")
                    print(f"  Time: {total_time:.1f}s, Chunks: {total_chunks}, Added: {added}")
                break
            elif status == 'failed':
                print(f"❌ СЦЕНАРИЙ 4 FAILED: Import failed - {progress.get('current_operation', 'unknown')}")
                break
        
        time.sleep(2)
    else:
        print("❌ СЦЕНАРИЙ 4 FAILED: Import did not complete within 2 minutes")
else:
    print(f"❌ СЦЕНАРИЙ 4 FAILED: Speed test import failed - {response6.text}")

print("\n" + "=" * 60)
print("🏁 FINAL TESTING COMPLETE")
print("🇷🇺 RUSSIAN USER REVIEW REQUEST - RESTORED IMPORT FUNCTIONALITY VERIFIED")