import asyncio
import sqlite3
import sys
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator
from accurate_speed_test import AccurateSpeedTester

async def test():
    # Берем 10 узлов ping_ok (знаем что они работают)
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_ok" LIMIT 10')
    nodes = cursor.fetchall()
    conn.close()
    
    print('=' * 80)
    print('ПРОВЕРКА ЦЕПОЧКИ НА ИЗВЕСТНЫХ РАБОЧИХ УЗЛАХ')
    print('=' * 80)
    print(f'\nТестирую {len(nodes)} узлов со статусом ping_ok...\n')
    
    speed_ok_count = 0
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        print(f'[{i}/10] {ip}')
        
        # SPEED OK тест (PING LIGHT и PING OK уже прошли)
        try:
            speed_result = await asyncio.wait_for(
                AccurateSpeedTester.accurate_speed_test(ip, login, password, sample_kb=32, timeout=10.0),
                timeout=12.0
            )
            
            if speed_result.get('success'):
                down = speed_result.get('download_mbps', 0)
                up = speed_result.get('upload_mbps', 0)
                ping = speed_result.get('ping_ms', 0)
                print(f'  ✅ SPEED OK: ↓{down:.2f} Mbps, ↑{up:.2f} Mbps, {ping:.0f}ms')
                speed_ok_count += 1
            else:
                print(f'  ❌ SPEED FAILED: {speed_result.get("message", "")[:60]}')
        except Exception as e:
            print(f'  ❌ ERROR: {str(e)[:60]}')
    
    print(f'\n{"=" * 80}')
    print(f'РЕЗУЛЬТАТ: {speed_ok_count}/10 узлов прошли SPEED OK тест')
    print(f'{"=" * 80}')

asyncio.run(test())
