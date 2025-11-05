#!/usr/bin/env python3

import requests
import json
import time

# Configuration
BASE_URL = "https://memory-mcp.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api"

def login():
    """Login and get token"""
    login_data = {"username": "admin", "password": "admin"}
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get('access_token')
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def test_regular_import(token):
    """Test 1: Regular Import (small files <200KB)"""
    print("\n🔥 ТЕСТ 1: Regular Import (малые файлы <200KB)")
    
    # Generate 50 lines of Format 7 (IP:Login:Pass)
    test_lines = []
    for i in range(50):
        test_lines.append(f"5.78.{i//256}.{i%256+1}:admin:pass{i}")
    
    test_data = "\n".join(test_lines)
    data_size = len(test_data.encode('utf-8'))
    
    print(f"📊 Test data: {len(test_lines)} lines, {data_size} bytes ({data_size/1024:.1f}KB)")
    
    import_data = {
        "data": test_data,
        "protocol": "pptp"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(f"{API_URL}/nodes/import", json=import_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            report = result.get('report', {})
            added = report.get('added', 0)
            skipped = report.get('skipped_duplicates', 0)
            errors = report.get('format_errors', 0)
            has_session_id = 'session_id' in result and result['session_id'] is not None
            
            print(f"✅ SUCCESS: {added} added, {skipped} skipped, {errors} errors")
            print(f"   Session ID: {result.get('session_id', 'None')} (should be None for small files)")
            
            if not has_session_id and added > 0:
                print("✅ PASSED: Regular processing (no session_id)")
                return True
            else:
                print("❌ FAILED: Expected regular processing")
                return False
        else:
            print(f"❌ FAILED: {result}")
            return False
    else:
        print(f"❌ FAILED: HTTP {response.status_code} - {response.text}")
        return False

def test_chunked_import(token):
    """Test 2: Chunked Import (large files >200KB)"""
    print("\n🔥 ТЕСТ 2: Chunked Import (большие файлы >200KB)")
    
    # Generate 1000 lines of Format 7 to ensure >200KB
    test_lines = []
    for i in range(1000):
        ip_a = 10 + (i // 65536)
        ip_b = (i // 256) % 256
        ip_c = i % 256
        test_lines.append(f"{ip_a}.{ip_b}.{ip_c}.1:admin:pass{i}")
    
    test_data = "\n".join(test_lines)
    data_size = len(test_data.encode('utf-8'))
    
    print(f"📊 Test data: {len(test_lines)} lines, {data_size} bytes ({data_size/1024:.1f}KB)")
    
    import_data = {
        "data": test_data,
        "protocol": "pptp"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(f"{API_URL}/nodes/import-chunked", json=import_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            session_id = result.get('session_id')
            total_chunks = result.get('total_chunks', 0)
            progress_url = result.get('progress_url', '')
            
            print(f"✅ SUCCESS: session_id={session_id}, total_chunks={total_chunks}")
            print(f"   Progress URL: {progress_url}")
            
            if session_id and total_chunks > 0:
                print("✅ PASSED: Chunked processing started")
                return session_id
            else:
                print("❌ FAILED: Missing session_id or total_chunks")
                return None
        else:
            print(f"❌ FAILED: {result}")
            return None
    else:
        print(f"❌ FAILED: HTTP {response.status_code} - {response.text}")
        return None

def test_progress_tracking(token, session_id):
    """Test 3: Progress Tracking"""
    print("\n🔥 ТЕСТ 3: Progress Tracking")
    
    if not session_id:
        print("❌ FAILED: No session_id provided")
        return False
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # Wait a moment for processing to start
    print("⏳ Waiting for processing to start...")
    time.sleep(3)
    
    response = requests.get(f"{API_URL}/import/progress/{session_id}", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        
        # Check for required progress fields
        required_fields = ['session_id', 'total_chunks', 'processed_chunks', 'status', 'added', 'skipped', 'errors']
        missing_fields = [field for field in required_fields if field not in result]
        
        if not missing_fields:
            status = result.get('status', 'unknown')
            processed_chunks = result.get('processed_chunks', 0)
            total_chunks = result.get('total_chunks', 0)
            added = result.get('added', 0)
            skipped = result.get('skipped', 0)
            errors = result.get('errors', 0)
            
            print(f"✅ SUCCESS: status={status}, processed_chunks={processed_chunks}/{total_chunks}")
            print(f"   Statistics: added={added}, skipped={skipped}, errors={errors}")
            print("✅ PASSED: Progress tracking working")
            return True
        else:
            print(f"❌ FAILED: Missing required fields: {missing_fields}")
            return False
    else:
        print(f"❌ FAILED: HTTP {response.status_code} - {response.text}")
        return False

def main():
    print("🚀 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Импорт узлов через API")
    print("=" * 80)
    print("КОНТЕКСТ: Пользователь не может импортировать узлы ни через текстовый буфер, ни через файл.")
    print("ТЕСТИРУЕМЫЕ СЦЕНАРИИ:")
    print("1. Regular Import (малые файлы <200KB) - POST /api/nodes/import")
    print("2. Chunked Import (большие файлы >200KB) - POST /api/nodes/import-chunked")
    print("3. Progress Tracking - GET /api/import/progress/{session_id}")
    print("ФОРМАТ ДАННЫХ: Format 7 (IP:Login:Pass)")
    print("=" * 80)
    
    # Login
    token = login()
    if not token:
        print("❌ Cannot proceed without authentication")
        return False
    
    # Run tests
    test1_passed = test_regular_import(token)
    session_id = test_chunked_import(token)
    test2_passed = session_id is not None
    test3_passed = test_progress_tracking(token, session_id)
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    
    tests_passed = sum([test1_passed, test2_passed, test3_passed])
    total_tests = 3
    
    print(f"📊 Результат: {tests_passed}/{total_tests} тестов пройдено ({(tests_passed/total_tests)*100:.1f}%)")
    
    if test1_passed:
        print("✅ ТЕСТ 1: Regular Import - ПРОЙДЕН")
    else:
        print("❌ ТЕСТ 1: Regular Import - НЕ ПРОЙДЕН")
    
    if test2_passed:
        print("✅ ТЕСТ 2: Chunked Import - ПРОЙДЕН")
    else:
        print("❌ ТЕСТ 2: Chunked Import - НЕ ПРОЙДЕН")
    
    if test3_passed:
        print("✅ ТЕСТ 3: Progress Tracking - ПРОЙДЕН")
    else:
        print("❌ ТЕСТ 3: Progress Tracking - НЕ ПРОЙДЕН")
    
    if tests_passed == total_tests:
        print("\n🎉 ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Импорт узлов работает корректно через оба endpoint")
        return True
    else:
        print(f"\n❌ {total_tests - tests_passed} тестов не пройдено")
        print("❌ Требуется исправление функциональности импорта")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)