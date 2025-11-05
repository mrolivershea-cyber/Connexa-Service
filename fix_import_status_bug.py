#!/usr/bin/env python3
"""
Fix Status Assignment Bug - Migration Script

This script fixes the critical bug where imported nodes got wrong status.
According to user requirements:
- All newly imported nodes should have 'not_tested' status by default
- Nodes should only get 'online' status after successful manual service launch
- This script changes incorrectly assigned 'online' nodes back to 'not_tested'

User reported: 2,336 nodes with 2,332 having 'online' status (should be 'not_tested')
"""

import sys
import os

# Add backend to Python path and use backend database
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from database import get_db, Node
from collections import Counter
from datetime import datetime

def main():
    db = next(get_db())
    
    print("=== Status Assignment Bug Fix ===")
    print("Analyzing current database status...")
    
    # Get current status distribution
    nodes = db.query(Node).all()
    statuses = [node.status for node in nodes]
    status_counts = Counter(statuses)
    
    print(f"\nCurrent status distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    print(f"Total nodes: {len(nodes)}")
    
    # Find nodes that likely were incorrectly imported with 'online' status
    # These are nodes that have 'online' status but no recent service activity
    online_nodes = db.query(Node).filter(Node.status == 'online').all()
    print(f"\nAnalyzing {len(online_nodes)} nodes with 'online' status...")
    
    # Criteria for identifying incorrectly imported nodes:
    # 1. Status is 'online' 
    # 2. No last_check timestamp (never actually tested)
    # 3. Created recently (likely from the import)
    
    incorrectly_online_nodes = []
    correctly_online_nodes = []
    
    for node in online_nodes:
        # If node has no last_check, it was likely never actually tested
        if node.last_check is None:
            incorrectly_online_nodes.append(node)
        else:
            correctly_online_nodes.append(node)
    
    print(f"\nAnalysis results:")
    print(f"  Incorrectly 'online' nodes (no test history): {len(incorrectly_online_nodes)}")
    print(f"  Correctly 'online' nodes (have test history): {len(correctly_online_nodes)}")
    
    if incorrectly_online_nodes:
        print(f"\nSample of incorrectly 'online' nodes:")
        for i, node in enumerate(incorrectly_online_nodes[:5]):
            print(f"  {i+1}. {node.ip} - Status: {node.status}, Last Check: {node.last_check}, Created: {node.created_at}")
        
        # Automatic fix for non-interactive environment
        print(f"\nAutomatically fixing {len(incorrectly_online_nodes)} nodes from 'online' to 'not_tested'")
        print("These appear to be nodes that were incorrectly assigned 'online' status during import.")
        print("Nodes with actual test history will remain 'online'.")
        
        print("\nFixing node statuses...")
        fixed_count = 0
        for node in incorrectly_online_nodes:
            node.status = 'not_tested'
            fixed_count += 1
            if fixed_count % 100 == 0:
                print(f"  Fixed {fixed_count}/{len(incorrectly_online_nodes)} nodes...")
        
        db.commit()
        
        print(f"\n✅ Successfully fixed {fixed_count} nodes!")
        
        # Show final status distribution
        print("\nFinal status distribution:")
        nodes = db.query(Node).all()
        statuses = [node.status for node in nodes]
        status_counts = Counter(statuses)
        
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")
    else:
        print("\n✅ No incorrectly assigned 'online' nodes found!")
    
    print("\n=== Fix Complete ===")

if __name__ == "__main__":
    main()