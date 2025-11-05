import asyncio
import sqlite3
import sys
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test():
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_light" LIMIT 100')
    nodes = cursor.fetchall()
    conn.close()
    
    print('Тестирую 100 узлов ping_light...\n')
    
    success = 0
    invalid_creds = 0
    errors = 0
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        try:
            result = await asyncio.wait_for(
                PPTPAuthenticator.authentic_pptp_test(ip, login, password, timeout=8.0),
                timeout=10.0
            )
            
            if result.get('success'):
                success += 1
                print(f'[{i}/100] ✅ {ip}')
            else:
                if 'Invalid credentials' in result.get('message', ''):
                    invalid_creds += 1
                else:
                    errors += 1
        except:
            errors += 1
        
        if i % 20 == 0:
            print(f'Прогресс: {i}/100 - SUCCESS: {success}, Invalid: {invalid_creds}, Errors: {errors}')
    
    print(f'\n{"=" * 80}')
    print(f'РЕЗУЛЬТАТЫ НА 100 УЗЛАХ:')
    print(f'✅ SUCCESS: {success} ({success}%)')
    print(f'❌ Invalid credentials: {invalid_creds} ({invalid_creds}%)')
    print(f'❌ Errors/Timeout: {errors} ({errors}%)')
    print('=' * 80)
    
    # Экстраполяция на 1529
    print(f'\nЭКСТРАПОЛЯЦИЯ НА 1529 УЗЛОВ:')
    print(f'Ожидаемых SUCCESS: ~{int(1529 * success / 100)} узлов')
    print(f'Ожидаемых Invalid credentials: ~{int(1529 * invalid_creds / 100)} узлов')
    print(f'Ожидаемых Errors: ~{int(1529 * errors / 100)} узлов')

asyncio.run(test())
