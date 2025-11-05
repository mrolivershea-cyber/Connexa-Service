#!/usr/bin/env python3

import requests
import json

# Login and get token
login_data = {"username": "admin", "password": "admin"}
login_response = requests.post("https://memory-mcp.preview.emergentagent.com/api/auth/login", json=login_data)
token = login_response.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

print("🔥 Testing SOCKS with filters...")

# Test SOCKS Start with filters
socks_start_data = {
    "filters": {"status": "ping_light"},
    "select_all": True
}

print(f"📤 SOCKS Start request: {socks_start_data}")
socks_response = requests.post("https://memory-mcp.preview.emergentagent.com/api/socks/start", json=socks_start_data, headers=headers)
print(f"📥 SOCKS Start response: {socks_response.status_code} - {socks_response.text}")

# Test SOCKS Stop with filters
socks_stop_data = {
    "filters": {"status": "ping_failed"},
    "select_all": True
}

print(f"📤 SOCKS Stop request: {socks_stop_data}")
socks_response = requests.post("https://memory-mcp.preview.emergentagent.com/api/socks/stop", json=socks_stop_data, headers=headers)
print(f"📥 SOCKS Stop response: {socks_response.status_code} - {socks_response.text}")