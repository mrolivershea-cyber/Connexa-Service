import asyncio
import sqlite3
import sys
sys.path.insert(0, '/app/backend')

from accurate_speed_test import AccurateSpeedTester

async def test():
    # Берем известные рабочие узлы ping_ok
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_ok" LIMIT 10')
    nodes = cursor.fetchall()
    conn.close()
    
    print('=' * 80)
    print('ТЕСТИРОВАНИЕ ИСПРАВЛЕННОГО SPEED OK')
    print('=' * 80)
    print(f'\nТестирую {len(nodes)} узлов...\n')
    
    success_count = 0
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        print(f'[{i}/10] {ip}')
        
        try:
            result = await asyncio.wait_for(
                AccurateSpeedTester.accurate_speed_test(ip, login, password, sample_kb=32, timeout=10.0),
                timeout=12.0
            )
            
            if result.get('success'):
                down = result.get('download_mbps', 0)
                up = result.get('upload_mbps', 0)
                ping = result.get('ping_ms', 0)
                print(f'  ✅ SUCCESS: ↓{down:.2f} Mbps, ↑{up:.2f} Mbps, {ping:.0f}ms')
                success_count += 1
            else:
                print(f'  ❌ FAILED: {result.get("message", result.get("error", "unknown"))[:50]}')
        except Exception as e:
            print(f'  ❌ ERROR: {str(e)[:50]}')
    
    print(f'\n{"=" * 80}')
    print(f'РЕЗУЛЬТАТ: {success_count}/10 узлов прошли SPEED OK')
    print(f'{"=" * 80}')
    
    if success_count > 0:
        print('\n✅ SPEED OK РАБОТАЕТ!')
    else:
        print('\n❌ SPEED OK НЕ РАБОТАЕТ')

asyncio.run(test())
