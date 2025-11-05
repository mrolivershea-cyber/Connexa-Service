import asyncio
import sqlite3
import sys
import time
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator
from accurate_speed_test import AccurateSpeedTester

async def test():
    # Берем 20 узлов ping_light для полной цепочки
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_light" LIMIT 20')
    nodes = cursor.fetchall()
    conn.close()
    
    print('=' * 80)
    print('ПОЛНАЯ ЦЕПОЧКА: PING LIGHT → PING OK → SPEED OK')
    print('=' * 80)
    print(f'\nТестирую {len(nodes)} узлов...\n')
    
    results = {
        'ping_light': len(nodes),  # Все уже ping_light
        'ping_ok': 0,
        'speed_ok': 0
    }
    
    speed_ok_nodes = []
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        print(f'[{i}/20] {ip}')
        print(f'  ✅ PING LIGHT: OK (уже протестирован)')
        
        # ЭТАП 2: PING OK
        try:
            ping_ok_result = await asyncio.wait_for(
                PPTPAuthenticator.authentic_pptp_test(ip, login, password, timeout=8.0),
                timeout=10.0
            )
            
            if ping_ok_result.get('success'):
                print(f'  ✅ PING OK: SUCCESS')
                results['ping_ok'] += 1
                
                # ЭТАП 3: SPEED OK
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
                        results['speed_ok'] += 1
                        speed_ok_nodes.append({'ip': ip, 'down': down, 'up': up, 'ping': ping})
                    else:
                        print(f'  ❌ SPEED FAILED')
                except:
                    print(f'  ❌ SPEED ERROR')
            else:
                print(f'  ❌ PING OK FAILED: {ping_ok_result.get("message", "")[:40]}')
        except:
            print(f'  ❌ PING OK ERROR')
    
    print(f'\n{"=" * 80}')
    print('ИТОГОВЫЙ ОТЧЕТ')
    print('=' * 80)
    print(f'Протестировано: 20 узлов')
    print(f'✅ PING LIGHT: 20 (100%)')
    print(f'✅ PING OK: {results["ping_ok"]} ({results["ping_ok"]*100/20:.1f}%)')
    print(f'✅ SPEED OK: {results["speed_ok"]} ({results["speed_ok"]*100/20:.1f}%)')
    
    if speed_ok_nodes:
        print(f'\nПОЛНОСТЬЮ РАБОЧИЕ УЗЛЫ (прошли все 3 этапа):')
        for node in speed_ok_nodes[:5]:
            print(f'  {node["ip"]}: ↓{node["down"]:.2f} Mbps, ↑{node["up"]:.2f} Mbps, {node["ping"]:.0f}ms')

asyncio.run(test())
