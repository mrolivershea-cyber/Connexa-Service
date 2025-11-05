#!/usr/bin/env python3
"""
Test import process to identify duplication issue
"""
import sys
sys.path.insert(0, '/app/backend')

from server import parse_nodes_text, process_parsed_nodes_bulk
from database import get_db

# Read file
with open('/app/PPTP.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Parse
print("=" * 60)
print("STEP 1: PARSING")
print("=" * 60)
parsed_result = parse_nodes_text(text)
print(f"Parsed nodes: {len(parsed_result['nodes'])}")
print(f"Format errors: {len(parsed_result['format_errors'])}")

# Check unique IPs in parsed result
ips_in_parsed = [node['ip'] for node in parsed_result['nodes']]
unique_ips_parsed = set(ips_in_parsed)
print(f"Unique IPs in parsed nodes: {len(unique_ips_parsed)}")
print(f"Duplicate count in parse: {len(ips_in_parsed) - len(unique_ips_parsed)}")

# Check duplicates by (IP, login, password)
seen = set()
duplicate_configs = []
for node in parsed_result['nodes']:
    key = (node['ip'], node.get('login', ''), node.get('password', ''))
    if key in seen:
        duplicate_configs.append(key)
    seen.add(key)

print(f"Duplicate configurations (IP+login+pass): {len(duplicate_configs)}")
print(f"Unique configurations in parsed nodes: {len(seen)}")

# Sample duplicates
if duplicate_configs:
    print("\nSample duplicate configurations:")
    for ip, login, password in list(duplicate_configs)[:5]:
        print(f"  {ip}:{login}:{password}")

# Now test with DB processing
print("\n" + "=" * 60)
print("STEP 2: SIMULATING DB PROCESSING (DRY RUN)")
print("=" * 60)

db = next(get_db())

# Create a test scenario: count how many would be added/skipped
from collections import defaultdict
stats = {
    'would_add': 0,
    'would_skip_duplicate_in_import': 0,
    'would_skip_duplicate_in_db': 0
}

# STEP 1 OF process_parsed_nodes_bulk: Deduplicate within import
seen_in_import = set()
unique_in_import = []

for node_data in parsed_result['nodes']:
    node_key = (node_data['ip'], node_data.get('login', ''), node_data.get('password', ''))
    
    if node_key in seen_in_import:
        stats['would_skip_duplicate_in_import'] += 1
        continue
    
    seen_in_import.add(node_key)
    unique_in_import.append(node_data)

print(f"After internal deduplication: {len(unique_in_import)} unique nodes")
print(f"Skipped duplicates within import: {stats['would_skip_duplicate_in_import']}")

# STEP 2: Check against DB
from server import check_node_duplicate

for node_data in unique_in_import:
    dup_result = check_node_duplicate(
        db, 
        node_data['ip'], 
        node_data['login'], 
        node_data['password']
    )
    
    if dup_result["action"] == "add" or dup_result["action"] == "replace":
        stats['would_add'] += 1
    elif dup_result["action"] == "skip":
        stats['would_skip_duplicate_in_db'] += 1

print(f"\nFinal statistics:")
print(f"  Would add new nodes: {stats['would_add']}")
print(f"  Would skip (already in DB): {stats['would_skip_duplicate_in_db']}")
print(f"  Total unique configs from file: {len(unique_in_import)}")
print(f"\nExpected total in DB after import: {stats['would_add'] + db.query(Node).count()}")

# Import the database.py Node class
from database import Node
current_db_count = db.query(Node).count()
print(f"Current DB count: {current_db_count}")
print(f"Expected final count: {current_db_count} + {stats['would_add']} = {current_db_count + stats['would_add']}")
