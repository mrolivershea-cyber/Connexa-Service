#!/usr/bin/env python3
"""
Fix nodes stuck in 'checking' status
"""

import sqlite3
from datetime import datetime, timezone

def fix_checking_status():
    """Reset all nodes stuck in 'checking' status back to their previous state"""
    
    # Connect to database
    conn = sqlite3.connect('/app/backend/connexa.db')
    cursor = conn.cursor()
    
    try:
        # Get count of nodes in checking status
        cursor.execute("SELECT COUNT(*) FROM nodes WHERE status = 'checking'")
        checking_count = cursor.fetchone()[0]
        
        print(f"Found {checking_count} nodes stuck in 'checking' status")
        
        if checking_count > 0:
            # Reset checking nodes to not_tested status
            current_time = datetime.now(timezone.utc).isoformat()
            
            cursor.execute("""
                UPDATE nodes 
                SET status = 'not_tested', 
                    last_update = ?,
                    last_check = ?
                WHERE status = 'checking'
            """, (current_time, current_time))
            
            print(f"✅ Reset {checking_count} nodes from 'checking' to 'not_tested'")
            
        # Get updated statistics
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM nodes 
            GROUP BY status 
            ORDER BY COUNT(*) DESC
        """)
        
        stats = cursor.fetchall()
        
        print("\n📊 Updated Node Status Distribution:")
        total = 0
        for status, count in stats:
            print(f"  {status}: {count}")
            total += count
        print(f"  TOTAL: {total}")
        
        # Commit changes
        conn.commit()
        print(f"\n✅ Database updated successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_checking_status()