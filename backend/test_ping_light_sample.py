import asyncio
import sqlite3
import sys
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test():
    # Берем 50 случайных ping_light узлов
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_light" ORDER BY RANDOM() LIMIT 50')
    nodes = cursor.fetchall()
    conn.close()
    
    print('=' * 80)
    print('ПРОВЕРКА: ПОЧЕМУ PING_LIGHT НЕ ПРОХОДЯТ PING OK')
    print('=' * 80)
    print(f'\nТестирую 50 случайных узлов...\n')
    
    results = {
        'success': [],
        'invalid_credentials': [],
        'connection_error': [],
        'timeout': [],
        'other': []
    }
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        try:
            result = await asyncio.wait_for(
                PPTPAuthenticator.authentic_pptp_test(ip, login, password, timeout=8.0),
                timeout=10.0
            )
            
            if result.get('success'):
                results['success'].append(ip)
                print(f'[{i}/50] ✅ {ip} - SUCCESS')
            else:
                msg = result.get('message', '')
                if 'Invalid credentials' in msg or 'call_result' in msg:
                    results['invalid_credentials'].append((ip, msg))
                    if i <= 10:  # Показываем первые 10
                        print(f'[{i}/50] ❌ {ip} - Invalid credentials')
                elif 'Connection' in msg:
                    results['connection_error'].append((ip, msg))
                    if i <= 10:
                        print(f'[{i}/50] ❌ {ip} - Connection error')
                elif 'timeout' in msg.lower():
                    results['timeout'].append((ip, msg))
                    if i <= 10:
                        print(f'[{i}/50] ❌ {ip} - Timeout')
                else:
                    results['other'].append((ip, msg))
                    if i <= 10:
                        print(f'[{i}/50] ❌ {ip} - {msg[:40]}')
        except asyncio.TimeoutError:
            results['timeout'].append((ip, 'Test timeout'))
            if i <= 10:
                print(f'[{i}/50] ❌ {ip} - Test timeout')
        except Exception as e:
            results['other'].append((ip, str(e)))
            if i <= 10:
                print(f'[{i}/50] ❌ {ip} - {str(e)[:40]}')
        
        if i % 10 == 0:
            print(f'\nПрогресс: {i}/50')
    
    print(f'\n{"=" * 80}')
    print('ДЕТАЛЬНЫЙ ОТЧЕТ')
    print('=' * 80)
    print(f'Протестировано: 50 узлов')
    print(f'✅ SUCCESS: {len(results["success"])} ({len(results["success"])*100/50:.1f}%)')
    print(f'❌ Invalid credentials: {len(results["invalid_credentials"])} ({len(results["invalid_credentials"])*100/50:.1f}%)')
    print(f'❌ Connection error: {len(results["connection_error"])} ({len(results["connection_error"])*100/50:.1f}%)')
    print(f'❌ Timeout: {len(results["timeout"])} ({len(results["timeout"])*100/50:.1f}%)')
    print(f'❌ Other: {len(results["other"])} ({len(results["other"])*100/50:.1f}%)')
    
    if results['success']:
        print(f'\n✅ РАБОЧИЕ УЗЛЫ ({len(results["success"])}):')
        for ip in results['success'][:5]:
            print(f'  {ip}')
    
    if results['invalid_credentials']:
        print(f'\n❌ ПРИМЕРЫ INVALID CREDENTIALS:')
        for ip, msg in results['invalid_credentials'][:3]:
            print(f'  {ip}: {msg[:60]}')
    
    if results['connection_error']:
        print(f'\n❌ ПРИМЕРЫ CONNECTION ERROR:')
        for ip, msg in results['connection_error'][:3]:
            print(f'  {ip}: {msg[:60]}')

asyncio.run(test())
