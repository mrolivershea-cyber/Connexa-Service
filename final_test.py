#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app/backend')
from server import parse_nodes_text

# Parse PPTP.txt
with open('/app/PPTP.txt', 'r', encoding='utf-8') as f:
    text = f.read()

result = parse_nodes_text(text)
nodes = result['nodes']

print("=== PPTP.txt ANALYSIS ===")
print(f"Total nodes parsed: {len(nodes)}")

# Deduplicate by (IP, login, password)
seen = {}
duplicates = []
for i, node in enumerate(nodes):
    key = (node['ip'], node.get('login', ''), node.get('password', ''))
    if key in seen:
        duplicates.append((i, key, seen[key]))
    else:
        seen[key] = i

print(f"Unique configurations: {len(seen)}")
print(f"Duplicate entries: {len(duplicates)}")

# After deduplication in process_parsed_nodes_bulk
unique_nodes = list(seen.keys())
print(f"\nExpected nodes after internal dedup: {len(unique_nodes)}")

# Count unique IPs (regardless of credentials)
unique_ips = set(k[0] for k in unique_nodes)
print(f"Unique IPs (regardless of creds): {len(unique_ips)}")

# Find if there are IPs with different credentials
from collections import defaultdict
ip_to_creds = defaultdict(set)
for ip, login, password in unique_nodes:
    ip_to_creds[ip].add((login, password))

multiple_creds = {ip: creds for ip, creds in ip_to_creds.items() if len(creds) > 1}
print(f"IPs with multiple credentials: {len(multiple_creds)}")

if multiple_creds:
    print("\nSample IPs with different credentials:")
    for ip, creds in list(multiple_creds.items())[:5]:
        print(f"  {ip}: {len(creds)} different credential sets")
        for login, password in list(creds)[:3]:
            print(f"    {login}:{password}")

# Parse PPTP 2.txt for comparison
print("\n=== PPTP 2.txt ANALYSIS ===")
with open('/app/PPTP_2.txt', 'r', encoding='utf-8') as f:
    text2 = f.read()

result2 = parse_nodes_text(text2)
nodes2 = result2['nodes']

print(f"Total nodes parsed: {len(nodes2)}")

seen2 = {}
for node in nodes2:
    key = (node['ip'], node.get('login', ''), node.get('password', ''))
    seen2[key] = True

print(f"Unique configurations: {len(seen2)}")

# Count unique IPs
unique_ips2 = set(k[0] for k in seen2.keys())
print(f"Unique IPs: {len(unique_ips2)}")
