#!/usr/bin/env python3

import sqlite3

def fix_checking_status():
    """Fix nodes stuck in 'checking' status"""
    try:
        conn = sqlite3.connect('/app/backend/connexa.db')
        cursor = conn.cursor()
        
        # Count nodes in checking status
        cursor.execute("SELECT COUNT(*) FROM nodes WHERE status = 'checking'")
        checking_count = cursor.fetchone()[0]
        
        print(f"Found {checking_count} nodes stuck in 'checking' status")
        
        # Update them to not_tested
        cursor.execute("UPDATE nodes SET status = 'not_tested' WHERE status = 'checking'")
        updated_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"Updated {updated_count} nodes from 'checking' to 'not_tested'")
        return True
        
    except Exception as e:
        print(f"Error fixing checking status: {e}")
        return False

if __name__ == "__main__":
    fix_checking_status()