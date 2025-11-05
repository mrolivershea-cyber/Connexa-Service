#!/usr/bin/env python3
import requests
import json

# Read file
with open('/app/PPTP.txt', 'r', encoding='utf-8') as f:
    data = f.read()

# Get backend URL from env
backend_url = "http://localhost:8001"

# Login first
login_response = requests.post(
    f"{backend_url}/api/auth/login",
    json={"username": "admin", "password": "admin"}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print(f"✓ Logged in successfully")

# Import nodes
headers = {"Authorization": f"Bearer {token}"}
import_response = requests.post(
    f"{backend_url}/api/nodes/import",
    headers=headers,
    json={"data": data, "protocol": "pptp", "testing_mode": "no_test"}
)

if import_response.status_code != 200:
    print(f"Import failed: {import_response.status_code}")
    print(import_response.text)
    exit(1)

result = import_response.json()
print(f"\n=== IMPORT RESULTS ===")
print(f"Total processed: {result.get('total_processed')}")
print(f"Successfully parsed: {result.get('successfully_parsed')}")
print(f"Added: {result.get('added')}")
print(f"Skipped (duplicates): {result.get('skipped_duplicates')}")
print(f"Format errors: {result.get('format_errors')}")
print(f"Processing errors: {result.get('processing_errors')}")
print(f"\nSmart summary: {result.get('smart_summary')}")

# Verify DB count
stats_response = requests.get(f"{backend_url}/api/stats", headers=headers)
if stats_response.status_code == 200:
    stats = stats_response.json()
    print(f"\n=== DATABASE STATS ===")
    print(f"Total nodes in DB: {stats.get('total')}")
