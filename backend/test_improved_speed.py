import asyncio
import sqlite3
import sys
sys.path.insert(0, '/app/backend')

from accurate_speed_test import AccurateSpeedTester

async def test():
    # Берем узлы ping_ok
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_ok" LIMIT 10')
    nodes = cursor.fetchall()
    conn.close()
    
    print('=' * 80)
    print('ТЕСТИРОВАНИЕ УЛУЧШЕННОГО SPEED TEST')
    print('С множественными замерами и оценкой качества')
    print('=' * 80)
    print()
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        print(f'[{i}/10] Тестирую {ip}...')
        
        try:
            result = await asyncio.wait_for(
                AccurateSpeedTester.accurate_speed_test(ip, login, password, sample_kb=64, timeout=15.0),
                timeout=20.0
            )
            
            if result.get('success'):
                down = result.get('download_mbps', 0)
                up = result.get('upload_mbps', 0)
                ping = result.get('ping_ms', 0)
                jitter = result.get('jitter_ms', 0)
                print(f'  ✅ ↓{down:.2f} Mbps, ↑{up:.2f} Mbps, {ping:.0f}ms ping, {jitter:.0f}ms jitter')
            else:
                print(f'  ❌ {result.get("message", "failed")}')
        except Exception as e:
            print(f'  ❌ Error: {str(e)[:50]}')
    
    print(f'\n{"=" * 80}')
    print('Улучшения:')
    print('  - 5 ping тестов для стабильности')
    print('  - 3 throughput теста, используем median')
    print('  - Измеряем jitter для оценки качества')
    print('  - Download оценка с учетом ping и jitter')
    print('=' * 80)

asyncio.run(test())
