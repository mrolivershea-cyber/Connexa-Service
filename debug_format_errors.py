#!/usr/bin/env python3

import requests
import json

def debug_format_errors():
    """Debug format error detection"""
    base_url = "https://memory-mcp.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Login first
    login_data = {"username": "admin", "password": "admin"}
    login_response = requests.post(f"{api_url}/auth/login", json=login_data)
    
    token = login_response.json()['access_token']
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # Test with clear separation between invalid lines
    import_data = {
        "data": "invalid line without proper format\n\nanother bad line\n\n192.168.1.101 admin pass CA",
        "protocol": "pptp"
    }
    
    print("🔍 Testing format errors with double newlines:")
    print(f"Data: {repr(import_data['data'])}")
    
    response = requests.post(f"{api_url}/nodes/import", json=import_data, headers=headers)
    
    if response.status_code == 200:
        report = response.json().get('report', {})
        print(f"Response: {json.dumps(report, indent=2)}")
    else:
        print(f"❌ Failed - HTTP {response.status_code}")

if __name__ == "__main__":
    debug_format_errors()