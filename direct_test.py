#!/usr/bin/env python3

import sqlite3
import json
from datetime import datetime

def test_database_directly():
    """Test the database directly to verify workflow functionality"""
    print("🔥 TESTING WORKFLOW FUNCTIONALITY VIA DATABASE")
    print("=" * 60)
    
    try:
        # Connect to the database
        conn = sqlite3.connect('/app/backend/connexa.db')
        cursor = conn.cursor()
        
        # Test 1: Check if the required tables and columns exist
        print("\n📋 STEP 1: Database Schema Verification")
        
        # Check nodes table structure
        cursor.execute("PRAGMA table_info(nodes)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = ['id', 'ip', 'login', 'password', 'status', 'last_update', 
                          'socks_ip', 'socks_port', 'socks_login', 'socks_password', 'ovpn_config']
        
        missing_columns = [col for col in required_columns if col not in column_names]
        
        if missing_columns:
            print(f"   ❌ Missing columns: {missing_columns}")
            return False
        else:
            print(f"   ✅ All required columns present: {len(required_columns)} columns")
        
        # Test 2: Check current database state
        print("\n📊 STEP 2: Database State Analysis")
        
        cursor.execute("SELECT status, COUNT(*) FROM nodes GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        total_nodes = sum(status_counts.values())
        print(f"   Total nodes: {total_nodes}")
        
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        # Test 3: Check for known working IPs
        print("\n🔍 STEP 3: Known Working IPs Verification")
        
        known_ips = ["72.197.30.147", "100.11.102.204", "100.16.39.213"]
        
        for ip in known_ips:
            cursor.execute("SELECT id, status, last_update FROM nodes WHERE ip = ?", (ip,))
            result = cursor.fetchone()
            
            if result:
                node_id, status, last_update = result
                print(f"   ✅ {ip}: Node {node_id}, Status: {status}, Last Update: {last_update}")
            else:
                print(f"   ❌ {ip}: Not found in database")
        
        # Test 4: Check SOCKS and OVPN data completeness
        print("\n🔌 STEP 4: SOCKS and OVPN Data Verification")
        
        cursor.execute("""
            SELECT COUNT(*) FROM nodes 
            WHERE status = 'online' 
            AND socks_ip IS NOT NULL 
            AND socks_port IS NOT NULL 
            AND socks_login IS NOT NULL 
            AND socks_password IS NOT NULL 
            AND ovpn_config IS NOT NULL
        """)
        
        complete_online_nodes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM nodes WHERE status = 'online'")
        total_online_nodes = cursor.fetchone()[0]
        
        print(f"   Online nodes with complete SOCKS/OVPN data: {complete_online_nodes}/{total_online_nodes}")
        
        if total_online_nodes > 0:
            # Show sample SOCKS data
            cursor.execute("""
                SELECT id, ip, socks_ip, socks_port, socks_login, LENGTH(ovpn_config) as ovpn_length
                FROM nodes 
                WHERE status = 'online' 
                AND socks_ip IS NOT NULL 
                LIMIT 3
            """)
            
            sample_nodes = cursor.fetchall()
            for node in sample_nodes:
                node_id, ip, socks_ip, socks_port, socks_login, ovpn_length = node
                print(f"   ✅ Node {node_id} ({ip}): SOCKS {socks_ip}:{socks_port} ({socks_login}), OVPN {ovpn_length} chars")
        
        # Test 5: Status Transition History Analysis
        print("\n🔄 STEP 5: Status Transition Analysis")
        
        # Check for nodes that have progressed through the workflow
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN status = 'not_tested' THEN 1 ELSE 0 END) as not_tested,
                SUM(CASE WHEN status = 'ping_ok' THEN 1 ELSE 0 END) as ping_ok,
                SUM(CASE WHEN status = 'ping_failed' THEN 1 ELSE 0 END) as ping_failed,
                SUM(CASE WHEN status = 'speed_ok' THEN 1 ELSE 0 END) as speed_ok,
                SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) as online,
                SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) as offline
            FROM nodes
        """)
        
        workflow_stats = cursor.fetchone()
        not_tested, ping_ok, ping_failed, speed_ok, online, offline = workflow_stats
        
        print(f"   Workflow progression:")
        print(f"   not_tested: {not_tested}")
        print(f"   ping_ok: {ping_ok}")
        print(f"   ping_failed: {ping_failed}")
        print(f"   speed_ok: {speed_ok}")
        print(f"   online: {online}")
        print(f"   offline: {offline}")
        
        # Test 6: Recent Activity Check
        print("\n⏰ STEP 6: Recent Activity Analysis")
        
        cursor.execute("""
            SELECT COUNT(*) FROM nodes 
            WHERE last_update > datetime('now', '-1 hour')
        """)
        
        recent_updates = cursor.fetchone()[0]
        print(f"   Nodes updated in last hour: {recent_updates}")
        
        if recent_updates > 0:
            cursor.execute("""
                SELECT ip, status, last_update 
                FROM nodes 
                WHERE last_update > datetime('now', '-1 hour')
                ORDER BY last_update DESC
                LIMIT 5
            """)
            
            recent_nodes = cursor.fetchall()
            print(f"   Recent activity:")
            for ip, status, last_update in recent_nodes:
                print(f"     {ip}: {status} at {last_update}")
        
        conn.close()
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 DATABASE ANALYSIS SUMMARY")
        print("=" * 60)
        
        workflow_working = (ping_ok > 0 or speed_ok > 0 or online > 0)
        socks_ovpn_working = (complete_online_nodes > 0)
        schema_complete = (len(missing_columns) == 0)
        
        print(f"✅ Database Schema Complete: {schema_complete}")
        print(f"✅ Workflow Functionality: {workflow_working}")
        print(f"✅ SOCKS/OVPN Generation: {socks_ovpn_working}")
        print(f"✅ Recent Activity: {recent_updates > 0}")
        
        overall_success = schema_complete and workflow_working
        
        if overall_success:
            print("\n🎉 DATABASE ANALYSIS: WORKFLOW FUNCTIONALITY VERIFIED")
        else:
            print("\n❌ DATABASE ANALYSIS: ISSUES DETECTED")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Database analysis failed: {e}")
        return False

def test_api_endpoints_via_curl():
    """Test API endpoints using curl commands"""
    print("\n🌐 TESTING API ENDPOINTS VIA CURL")
    print("=" * 60)
    
    import subprocess
    import json
    
    try:
        # Test 1: Login
        print("\n🔐 STEP 1: Authentication Test")
        
        login_cmd = [
            'curl', '-s', '-X', 'POST', 
            'http://127.0.0.1:8001/api/auth/login',
            '-H', 'Content-Type: application/json',
            '-d', '{"username": "admin", "password": "admin"}',
            '--connect-timeout', '5', '--max-time', '10'
        ]
        
        result = subprocess.run(login_cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and result.stdout:
            try:
                login_response = json.loads(result.stdout)
                if 'access_token' in login_response:
                    token = login_response['access_token']
                    print(f"   ✅ Login successful, token obtained")
                    
                    # Test 2: Get Stats
                    print("\n📊 STEP 2: Stats API Test")
                    
                    stats_cmd = [
                        'curl', '-s', '-X', 'GET',
                        'http://127.0.0.1:8001/api/stats',
                        '-H', f'Authorization: Bearer {token}',
                        '--connect-timeout', '5', '--max-time', '10'
                    ]
                    
                    stats_result = subprocess.run(stats_cmd, capture_output=True, text=True, timeout=15)
                    
                    if stats_result.returncode == 0 and stats_result.stdout:
                        try:
                            stats_response = json.loads(stats_result.stdout)
                            print(f"   ✅ Stats API working:")
                            print(f"     Total nodes: {stats_response.get('total', 'N/A')}")
                            print(f"     Not tested: {stats_response.get('not_tested', 'N/A')}")
                            print(f"     Online: {stats_response.get('online', 'N/A')}")
                            return True
                        except json.JSONDecodeError:
                            print(f"   ❌ Stats API returned invalid JSON: {stats_result.stdout}")
                    else:
                        print(f"   ❌ Stats API failed: {stats_result.stderr}")
                else:
                    print(f"   ❌ Login failed: {login_response}")
            except json.JSONDecodeError:
                print(f"   ❌ Login returned invalid JSON: {result.stdout}")
        else:
            print(f"   ❌ Login request failed: {result.stderr}")
        
        return False
        
    except Exception as e:
        print(f"   ❌ API testing failed: {e}")
        return False

def main():
    """Main test function"""
    print("🔥 COMPREHENSIVE WORKFLOW TESTING")
    print("=" * 80)
    
    # Test 1: Database Analysis
    db_success = test_database_directly()
    
    # Test 2: API Endpoints
    api_success = test_api_endpoints_via_curl()
    
    # Final Summary
    print("\n" + "=" * 80)
    print("🏁 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    print(f"Database Analysis: {'✅ PASSED' if db_success else '❌ FAILED'}")
    print(f"API Endpoints: {'✅ PASSED' if api_success else '❌ FAILED'}")
    
    overall_success = db_success and api_success
    
    if overall_success:
        print("\n🎉 ALL TESTS PASSED - WORKFLOW FUNCTIONALITY VERIFIED")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - ISSUES DETECTED")
        return 1

if __name__ == "__main__":
    exit(main())