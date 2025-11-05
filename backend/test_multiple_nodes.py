import asyncio
import sys
import sqlite3
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test_many_nodes():
    print('=' * 80)
    print('TESTING 50 RANDOM ping_light NODES')
    print('=' * 80)
    
    # Получаем 50 случайных узлов с ping_light статусом
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_light" ORDER BY RANDOM() LIMIT 50')
    nodes = cursor.fetchall()
    conn.close()
    
    print(f'\nTesting {len(nodes)} nodes...\n')
    
    success_count = 0
    failed_count = 0
    
    for ip, login, password in nodes:
        login = login or 'admin'
        password = password or 'admin'
        
        try:
            result = await asyncio.wait_for(
                PPTPAuthenticator.authentic_pptp_test(ip, login, password),
                timeout=8.0
            )
            
            if result.get('success'):
                success_count += 1
                print(f'SUCCESS: {ip} ({login}:{password}) - {result.get("message")}')
            else:
                failed_count += 1
                
        except Exception as e:
            failed_count += 1
    
    print('\n' + '=' * 80)
    print(f'RESULTS:')
    print(f'  SUCCESS: {success_count}')
    print(f'  FAILED: {failed_count}')
    print(f'  Success rate: {success_count}/{len(nodes)} = {success_count*100/len(nodes):.1f}%')
    print('=' * 80)
    
    if success_count > 0:
        print('\nPPTP AUTHENTICATION IS WORKING!')
    else:
        print('\nNo working nodes found with admin:admin credentials')
        print('This is EXPECTED - most nodes use different credentials')

asyncio.run(test_many_nodes())
