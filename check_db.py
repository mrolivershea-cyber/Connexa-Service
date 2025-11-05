#!/usr/bin/env python3

import sqlite3
from datetime import datetime

def check_database():
    try:
        conn = sqlite3.connect('/app/backend/connexa.db')
        cursor = conn.cursor()
        
        # Check the schema of the nodes table
        cursor.execute("PRAGMA table_info(nodes);")
        schema = cursor.fetchall()
        print("Nodes table schema:")
        for column in schema:
            print(f"  {column}")
        
        # Check recent nodes
        cursor.execute("SELECT id, ip, status, last_update, created_at FROM nodes ORDER BY id DESC LIMIT 10;")
        nodes = cursor.fetchall()
        print(f"\nRecent nodes (last 10):")
        for node in nodes:
            print(f"  ID: {node[0]}, IP: {node[1]}, Status: {node[2]}, Last Update: {node[3]}, Created: {node[4]}")
        
        # Check if all nodes have the same last_update
        cursor.execute("SELECT DISTINCT last_update FROM nodes;")
        distinct_timestamps = cursor.fetchall()
        print(f"\nDistinct last_update values:")
        for ts in distinct_timestamps:
            print(f"  {ts[0]}")
        
        # Count nodes by last_update
        cursor.execute("SELECT last_update, COUNT(*) FROM nodes GROUP BY last_update ORDER BY COUNT(*) DESC;")
        timestamp_counts = cursor.fetchall()
        print(f"\nTimestamp counts:")
        for ts, count in timestamp_counts:
            print(f"  {ts}: {count} nodes")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database()