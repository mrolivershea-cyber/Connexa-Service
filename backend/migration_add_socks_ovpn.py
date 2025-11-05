#!/usr/bin/env python3
"""
Migration script to add SOCKS and OVPN fields to existing nodes table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine
from sqlalchemy import text

def main():
    print("🔄 Adding SOCKS and OVPN columns to nodes table...")
    
    with engine.connect() as conn:
        try:
            # Add SOCKS fields
            conn.execute(text("ALTER TABLE nodes ADD COLUMN socks_ip VARCHAR(45)"))
            print("✅ Added socks_ip column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  socks_ip column already exists")
            else:
                print(f"❌ Error adding socks_ip: {e}")
        
        try:
            conn.execute(text("ALTER TABLE nodes ADD COLUMN socks_port INTEGER"))
            print("✅ Added socks_port column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  socks_port column already exists")
            else:
                print(f"❌ Error adding socks_port: {e}")
        
        try:
            conn.execute(text("ALTER TABLE nodes ADD COLUMN socks_login VARCHAR(100)"))
            print("✅ Added socks_login column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  socks_login column already exists")
            else:
                print(f"❌ Error adding socks_login: {e}")
        
        try:
            conn.execute(text("ALTER TABLE nodes ADD COLUMN socks_password VARCHAR(255)"))
            print("✅ Added socks_password column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  socks_password column already exists")
            else:
                print(f"❌ Error adding socks_password: {e}")
        
        try:
            conn.execute(text("ALTER TABLE nodes ADD COLUMN ovpn_config TEXT"))
            print("✅ Added ovpn_config column")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("⚠️  ovpn_config column already exists")
            else:
                print(f"❌ Error adding ovpn_config: {e}")
        
        conn.commit()
    
    print("✅ Migration completed successfully!")
    
    # Verify new schema
    print("\n🔍 Verifying new schema...")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    columns = inspector.get_columns('nodes')
    
    socks_ovpn_fields = ['socks_ip', 'socks_port', 'socks_login', 'socks_password', 'ovpn_config']
    for field in socks_ovpn_fields:
        found = any(col['name'] == field for col in columns)
        if found:
            print(f"✅ {field} field verified")
        else:
            print(f"❌ {field} field missing")

if __name__ == "__main__":
    main()