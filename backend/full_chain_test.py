import asyncio
import sqlite3
import sys
import time
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator
from accurate_speed_test import AccurateSpeedTester

async def test_full_chain():
    print('=' * 80)
    print('ПОЛНАЯ ПРОВЕРКА ЦЕПОЧКИ: PING LIGHT → PING OK → SPEED OK')
    print('=' * 80)
    
    # Берем 50 узлов ping_failed для полной цепочки
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_failed" LIMIT 50')
    nodes = cursor.fetchall()
    conn.close()
    
    print(f'\nТестирую {len(nodes)} узлов...\n')
    
    results = {
        'ping_light_success': [],
        'ping_ok_success': [],
        'speed_ok_success': []
    }
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        print(f'[{i}/50] Узел: {ip}')
        
        # ЭТАП 1: PING LIGHT (проверка TCP порта 1723)
        try:
            start = time.time()
            future = asyncio.open_connection(ip, 1723)
            reader, writer = await asyncio.wait_for(future, timeout=2.0)
            writer.close()
            await writer.wait_closed()
            ping_light_time = (time.time() - start) * 1000
            
            print(f'  ✅ PING LIGHT OK ({ping_light_time:.1f}ms)')
            results['ping_light_success'].append(ip)
            
            # ЭТАП 2: PING OK (PPTP авторизация)
            try:
                ping_ok_result = await asyncio.wait_for(
                    PPTPAuthenticator.authentic_pptp_test(ip, login, password, timeout=8.0),
                    timeout=10.0
                )
                
                if ping_ok_result.get('success'):
                    print(f'  ✅ PING OK SUCCESS ({login}:{password})')
                    results['ping_ok_success'].append(ip)
                    
                    # ЭТАП 3: SPEED OK (замер скорости)
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
                            results['speed_ok_success'].append({'ip': ip, 'down': down, 'up': up, 'ping': ping})
                        else:
                            print(f'  ❌ SPEED FAILED: {speed_result.get("message", "unknown")[:50]}')
                    except Exception as e:
                        print(f'  ❌ SPEED ERROR: {str(e)[:50]}')
                else:
                    print(f'  ❌ PING OK FAILED: {ping_ok_result.get("message", "")[:50]}')
            except Exception as e:
                print(f'  ❌ PING OK ERROR: {str(e)[:50]}')
        except:
            print(f'  ❌ PING LIGHT FAILED (port closed)')
        
        if i % 10 == 0:
            print(f'\nПрогресс: {i}/50 протестировано')
            print(f'  PING LIGHT: {len(results["ping_light_success"])}')
            print(f'  PING OK: {len(results["ping_ok_success"])}')
            print(f'  SPEED OK: {len(results["speed_ok_success"])}\n')
    
    print('\n' + '=' * 80)
    print('ИТОГОВЫЙ ОТЧЕТ')
    print('=' * 80)
    print(f'Протестировано узлов: 50')
    print(f'✅ PING LIGHT успешно: {len(results["ping_light_success"])} ({len(results["ping_light_success"])*100/50:.1f}%)')
    print(f'✅ PING OK успешно: {len(results["ping_ok_success"])} ({len(results["ping_ok_success"])*100/50:.1f}%)')
    print(f'✅ SPEED OK успешно: {len(results["speed_ok_success"])} ({len(results["speed_ok_success"])*100/50:.1f}%)')
    
    if results['speed_ok_success']:
        print(f'\nПОЛНОСТЬЮ РАБОЧИЕ УЗЛЫ (прошли все 3 этапа):')
        for node in results['speed_ok_success'][:5]:
            print(f'  {node["ip"]}: ↓{node["down"]:.2f} Mbps, ↑{node["up"]:.2f} Mbps, {node["ping"]:.0f}ms')

asyncio.run(test_full_chain())
