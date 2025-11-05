import asyncio
import sqlite3
import sys
sys.path.insert(0, '/app/backend')

from accurate_speed_test import AccurateSpeedTester

async def test():
    # Берем 20 узлов ping_ok
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_ok" LIMIT 20')
    nodes = cursor.fetchall()
    conn.close()
    
    print('=' * 80)
    print('ФИНАЛЬНЫЙ ТЕСТ SPEED OK НА 20 РАБОЧИХ УЗЛАХ')
    print('=' * 80)
    print(f'\nТестирую {len(nodes)} узлов со статусом ping_ok...\n')
    
    success = 0
    failed = 0
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        try:
            result = await asyncio.wait_for(
                AccurateSpeedTester.accurate_speed_test(ip, login, password, sample_kb=32, timeout=10.0),
                timeout=12.0
            )
            
            if result.get('success'):
                down = result.get('download_mbps', 0)
                up = result.get('upload_mbps', 0)
                ping = result.get('ping_ms', 0)
                print(f'[{i}/20] ✅ {ip}: ↓{down:.2f} Mbps, ↑{up:.2f} Mbps, {ping:.0f}ms')
                success += 1
            else:
                print(f'[{i}/20] ❌ {ip}: FAILED')
                failed += 1
        except:
            print(f'[{i}/20] ❌ {ip}: ERROR')
            failed += 1
    
    print(f'\n{"=" * 80}')
    print(f'SUCCESS: {success}/20 ({success*100/20:.1f}%)')
    print(f'FAILED: {failed}/20 ({failed*100/20:.1f}%)')
    print('=' * 80)

asyncio.run(test())
