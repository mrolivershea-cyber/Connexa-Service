import asyncio
import sys
import sqlite3
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test_100_nodes():
    print('=' * 80)
    print('TESTING 100 ping_light NODES WITH REAL PPTP')
    print('=' * 80)
    
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_light" LIMIT 100')
    nodes = cursor.fetchall()
    conn.close()
    
    print(f'\nTesting {len(nodes)} nodes...\n')
    
    success_nodes = []
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        try:
            result = await asyncio.wait_for(
                PPTPAuthenticator.authentic_pptp_test(ip, login, password),
                timeout=8.0
            )
            
            if result.get('success'):
                success_nodes.append((ip, login, password))
                print(f'{i}/100 SUCCESS: {ip} ({login}:{password})')
            
            if i % 10 == 0:
                print(f'Progress: {i}/100 tested, {len(success_nodes)} working')
                
        except Exception as e:
            pass
    
    print('\n' + '=' * 80)
    print(f'RESULTS: {len(success_nodes)} working nodes found out of 100')
    print('=' * 80)
    
    if success_nodes:
        print('\nWORKING NODES:')
        for ip, login, password in success_nodes:
            print(f'  {ip} ({login}:{password})')
    else:
        print('\nNo working nodes with admin:admin found in this batch')

asyncio.run(test_100_nodes())
