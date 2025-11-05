#!/usr/bin/env python3
"""
Test the chunked import functionality with large file processing
"""
import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8001"
USERNAME = "admin"
PASSWORD = "admin"

def login():
    """Login and get token"""
    login_data = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        raise Exception(f"Login failed: {response.text}")

def create_large_test_data(size_kb=600):
    """Create large test data in Format 7 (IP:Login:Pass)"""
    print(f"📊 Creating test data (~{size_kb}KB)...")
    
    lines = []
    target_size = size_kb * 1024  # Convert to bytes
    
    # Generate Format 7 entries: IP:Login:Pass
    ip_base = 192
    current_size = 0
    
    while current_size < target_size:
        for i in range(1, 255):  # IP range
            for j in range(1, 255):
                ip = f"{ip_base}.168.{i}.{j}"
                line = f"{ip}:admin:password{i}{j}\n"
                lines.append(line)
                current_size += len(line.encode('utf-8'))
                
                if current_size >= target_size:
                    break
            if current_size >= target_size:
                break
        ip_base += 1
        if ip_base > 223:  # Avoid broadcast ranges
            break
    
    test_data = ''.join(lines)
    actual_size = len(test_data.encode('utf-8'))
    print(f"✅ Generated {len(lines)} lines, {actual_size/1024:.1f}KB")
    
    return test_data

def test_regular_import(headers, data):
    """Test regular import (should be small enough)"""
    print("\n🧪 Testing regular import...")
    
    small_data = '\n'.join(data.split('\n')[:50])  # Just 50 lines
    size = len(small_data.encode('utf-8'))
    print(f"📊 Small data size: {size/1024:.1f}KB")
    
    import_data = {
        "data": small_data,
        "protocol": "pptp"
    }
    
    response = requests.post(f"{BASE_URL}/api/nodes/import", json=import_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Regular import successful: {result.get('message', 'No message')}")
        print(f"📊 Session ID: {result.get('session_id', 'None')}")
        return result
    else:
        print(f"❌ Regular import failed: {response.text}")
        return None

def test_chunked_import(headers, data):
    """Test chunked import with large data"""
    print("\n🧪 Testing chunked import...")
    
    size = len(data.encode('utf-8'))
    print(f"📊 Large data size: {size/1024:.1f}KB")
    
    import_data = {
        "data": data,
        "protocol": "pptp"
    }
    
    response = requests.post(f"{BASE_URL}/api/nodes/import", json=import_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        session_id = result.get('session_id')
        
        if session_id:
            print(f"✅ Chunked import started: {result.get('message', 'No message')}")
            print(f"📊 Session ID: {session_id}")
            print(f"📊 Total chunks: {result.get('total_chunks', 'Unknown')}")
            
            # Monitor progress
            return monitor_progress(headers, session_id)
        else:
            print(f"⚠️ No session_id returned - likely processed as regular import")
            return result
    else:
        print(f"❌ Chunked import failed: {response.text}")
        return None

def monitor_progress(headers, session_id):
    """Monitor import progress"""
    print(f"\n📊 Monitoring progress for session: {session_id}")
    
    start_time = time.time()
    last_progress = -1
    
    while True:
        try:
            response = requests.get(f"{BASE_URL}/api/import/progress/{session_id}", headers=headers)
            
            if response.status_code == 200:
                progress = response.json()
                
                current_progress = progress.get('processed_chunks', 0)
                total_chunks = progress.get('total_chunks', 0)
                status = progress.get('status', 'unknown')
                operation = progress.get('current_operation', '')
                
                # Only print if progress changed
                if current_progress != last_progress:
                    elapsed = time.time() - start_time
                    print(f"⏳ Progress: {current_progress}/{total_chunks} chunks ({current_progress/total_chunks*100:.1f}%) - {elapsed:.1f}s")
                    print(f"   Operation: {operation}")
                    
                    if progress.get('added', 0) > 0:
                        print(f"   Added: {progress.get('added', 0)}, Skipped: {progress.get('skipped', 0)}, Errors: {progress.get('errors', 0)}")
                    
                    last_progress = current_progress
                
                if status == 'completed':
                    elapsed = time.time() - start_time
                    print(f"\n✅ Import completed in {elapsed:.1f}s")
                    print(f"📊 Final results:")
                    print(f"   - Added: {progress.get('added', 0)}")
                    print(f"   - Skipped: {progress.get('skipped', 0)}")
                    print(f"   - Replaced: {progress.get('replaced', 0)}")
                    print(f"   - Errors: {progress.get('errors', 0)}")
                    return progress
                    
                elif status == 'failed':
                    print(f"\n❌ Import failed: {operation}")
                    return progress
                
                # Wait before next check
                time.sleep(2)
                
            else:
                print(f"❌ Progress check failed: {response.text}")
                break
                
        except Exception as e:
            print(f"❌ Error checking progress: {e}")
            break
    
    return None

def main():
    """Main test function"""
    print("🚀 Testing Chunked Import Functionality")
    print("=" * 50)
    
    try:
        # Login
        print("🔐 Logging in...")
        headers = login()
        print("✅ Login successful")
        
        # Create test data
        large_data = create_large_test_data(600)  # 600KB should trigger chunked processing
        
        # Test regular import first (small data)
        regular_result = test_regular_import(headers, large_data)
        
        # Test chunked import (large data)
        chunked_result = test_chunked_import(headers, large_data)
        
        print("\n" + "=" * 50)
        print("🎯 TEST SUMMARY:")
        
        if regular_result and not regular_result.get('session_id'):
            print("✅ Regular import: Working (no session_id as expected)")
        else:
            print("⚠️ Regular import: May have been chunked")
            
        if chunked_result and chunked_result.get('status') == 'completed':
            print("✅ Chunked import: Working (completed successfully)")
        else:
            print("❌ Chunked import: Failed or incomplete")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()