#!/usr/bin/env python3
"""
Create test PPTP data for demonstration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, Node
from datetime import datetime

def create_test_nodes():
    """Create test PPTP nodes"""
    db = SessionLocal()
    
    try:
        test_nodes = [
            # Working nodes (Group 1)
            {"ip": "178.62.193.45", "login": "user1", "password": "pass123", "provider": "DigitalOcean", "country": "US", "city": "New York"},
            {"ip": "142.93.198.76", "login": "user2", "password": "pass456", "provider": "Linode", "country": "UK", "city": "London"},
            {"ip": "159.89.214.89", "login": "user3", "password": "pass789", "provider": "Vultr", "country": "DE", "city": "Frankfurt"},
            {"ip": "167.99.92.33", "login": "user4", "password": "pass012", "provider": "AWS", "country": "SG", "city": "Singapore"},
            {"ip": "134.122.45.67", "login": "user5", "password": "pass345", "provider": "Hetzner", "country": "NL", "city": "Amsterdam"},
            
            # Non-working nodes (Group 2) - for testing failures
            {"ip": "10.0.0.1", "login": "test1", "password": "testpass", "provider": "Local", "country": "XX", "city": "Test"},
            {"ip": "192.168.1.1", "login": "test2", "password": "testpass2", "provider": "Local", "country": "XX", "city": "Test"},
            {"ip": "172.16.0.1", "login": "test3", "password": "testpass3", "provider": "Local", "country": "XX", "city": "Test"},
            {"ip": "169.254.1.1", "login": "test4", "password": "testpass4", "provider": "Local", "country": "XX", "city": "Test"},
            {"ip": "127.0.0.2", "login": "test5", "password": "testpass5", "provider": "Local", "country": "XX", "city": "Test"},
        ]
        
        for node_data in test_nodes:
            node = Node(
                ip=node_data["ip"],
                port=1723,  # Standard PPTP port
                login=node_data["login"],
                password=node_data["password"],
                provider=node_data["provider"],
                country=node_data["country"],
                city=node_data["city"],
                protocol="pptp",
                status="not_tested",
                last_update=datetime.utcnow()
            )
            db.add(node)
        
        db.commit()
        print(f"✅ Created {len(test_nodes)} test PPTP nodes")
        
        # Verify creation
        total_count = db.query(Node).count()
        print(f"✅ Total nodes in database: {total_count}")
        
    except Exception as e:
        print(f"❌ Error creating test nodes: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_nodes()