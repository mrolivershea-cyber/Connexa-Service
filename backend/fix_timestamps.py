#!/usr/bin/env python3
"""
Migration script to fix timestamps for existing nodes
Sets last_update to current time for all nodes that have NULL or old timestamps
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from database import SessionLocal, Node
from datetime import datetime

def fix_timestamps():
    db = SessionLocal()
    try:
        # Get all nodes with NULL last_update or very old timestamps
        nodes = db.query(Node).all()
        
        print(f"Found {len(nodes)} nodes in database")
        
        updated_count = 0
        for node in nodes:
            # Update last_update to current time
            node.last_update = datetime.utcnow()
            updated_count += 1
        
        db.commit()
        print(f"✅ Updated {updated_count} nodes with current timestamp")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting timestamp fix migration...")
    fix_timestamps()
    print("Migration complete!")
