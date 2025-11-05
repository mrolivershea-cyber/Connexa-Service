#!/usr/bin/env python3

import requests
import json
import time

def test_format_errors_and_deduplication():
    """Test format errors and deduplication logic"""
    base_url = "https://memory-mcp.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login first
    login_data = {"username": "admin", "password": "admin"}
    login_response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()['access_token']
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    print("🔍 Testing Format Errors")
    print("=" * 40)
    
    # Test format errors
    import_data = {
        "data": "invalid line without proper format\nanother bad line\n192.168.1.100 admin pass CA",
        "protocol": "pptp"
    }
    
    response = requests.post(f"{api_url}/nodes/import", json=import_data, headers=headers)
    
    if response.status_code == 200:
        report = response.json().get('report', {})
        added = report.get('added', 0)
        errors = report.get('format_errors', 0)
        
        print(f"Added: {added}, Format Errors: {errors}")
        
        if added >= 1 and errors >= 2:
            print("✅ Format errors test PASSED - 1 node created, 2 format errors logged")
            
            # Test GET /format-errors endpoint
            errors_response = requests.get(f"{api_url}/format-errors", headers=headers)
            
            if errors_response.status_code == 200:
                errors_data = errors_response.json()
                if errors_data.get('content'):
                    print("✅ GET /format-errors PASSED - Error details retrieved")
                else:
                    print("❌ GET /format-errors FAILED - No error content")
            else:
                print(f"❌ GET /format-errors FAILED - HTTP {errors_response.status_code}")
        else:
            print(f"❌ Format errors test FAILED - Expected 1 node + 2 errors, got {added} nodes + {errors} errors")
    else:
        print(f"❌ Format errors test FAILED - HTTP {response.status_code}")
    
    print("\n🔍 Testing Deduplication Logic")
    print("=" * 40)
    
    # Use unique IP for deduplication test
    timestamp = str(int(time.time()))[-2:]
    ip_suffix = str(int(timestamp) % 200 + 50)
    
    # First import
    import_data_1 = {
        "data": f"100.0.{ip_suffix}.1 admin admin CA",
        "protocol": "pptp"
    }
    
    response1 = requests.post(f"{api_url}/nodes/import", json=import_data_1, headers=headers)
    
    if response1.status_code == 200:
        report1 = response1.json().get('report', {})
        added1 = report1.get('added', 0)
        
        if added1 >= 1:
            print(f"✅ First import PASSED - {added1} node(s) added")
            
            # Second import (exact duplicate)
            response2 = requests.post(f"{api_url}/nodes/import", json=import_data_1, headers=headers)
            
            if response2.status_code == 200:
                report2 = response2.json().get('report', {})
                skipped2 = report2.get('skipped_duplicates', 0)
                
                if skipped2 >= 1:
                    print("✅ Deduplication PASSED - Second import skipped as duplicate (same IP+Login+Pass)")
                else:
                    print(f"❌ Deduplication FAILED - Expected duplicate to be skipped, got: {report2}")
            else:
                print(f"❌ Second import FAILED - HTTP {response2.status_code}")
        else:
            print(f"❌ First import FAILED - No nodes added: {report1}")
    else:
        print(f"❌ First import FAILED - HTTP {response1.status_code}")

if __name__ == "__main__":
    test_format_errors_and_deduplication()