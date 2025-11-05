#!/usr/bin/env python3

import requests
import json

# Configuration
BASE_URL = "https://memory-mcp.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

def login():
    """Login and get token"""
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def debug_regular_import(token):
    """Debug regular import with detailed logging"""
    print("\n🔍 DEBUG: Regular Import Analysis")
    
    # Test with a single Format 7 line first
    test_data = "5.78.100.1:testuser:testpass123"
    
    print(f"📊 Test data: '{test_data}'")
    print(f"📊 Data size: {len(test_data.encode('utf-8'))} bytes")
    
    import_data = {
        "data": test_data,
        "protocol": "pptp"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(f"{API_URL}/nodes/import", json=import_data, headers=headers)
    
    print(f"📊 Response status: {response.status_code}")
    print(f"📊 Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"📊 Full response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            report = result.get('report', {})
            print(f"📊 Report details:")
            print(f"   - total_processed: {report.get('total_processed', 'N/A')}")
            print(f"   - successfully_parsed: {report.get('successfully_parsed', 'N/A')}")
            print(f"   - added: {report.get('added', 'N/A')}")
            print(f"   - skipped_duplicates: {report.get('skipped_duplicates', 'N/A')}")
            print(f"   - format_errors: {report.get('format_errors', 'N/A')}")
            print(f"   - processing_errors: {report.get('processing_errors', 'N/A')}")
            
            details = report.get('details', {})
            if details:
                print(f"📊 Details:")
                for key, value in details.items():
                    print(f"   - {key}: {value}")
        else:
            print(f"❌ Import failed: {result}")
    else:
        print(f"❌ HTTP Error: {response.text}")

def check_existing_nodes(token):
    """Check if there are existing nodes that might cause duplicates"""
    print("\n🔍 DEBUG: Checking existing nodes")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # Check for nodes with similar IPs
    response = requests.get(f"{API_URL}/nodes?ip=5.78&limit=10", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        nodes = result.get('nodes', [])
        print(f"📊 Found {len(nodes)} nodes with IP starting with '5.78'")
        
        for i, node in enumerate(nodes[:5]):  # Show first 5
            print(f"   {i+1}. ID: {node.get('id')}, IP: {node.get('ip')}, Login: {node.get('login')}, Status: {node.get('status')}")
    else:
        print(f"❌ Failed to get nodes: {response.text}")

def main():
    print("🔍 DEBUG: Import Functionality Analysis")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        print("❌ Cannot proceed without authentication")
        return False
    
    # Check existing nodes first
    check_existing_nodes(token)
    
    # Debug regular import
    debug_regular_import(token)

if __name__ == "__main__":
    main()