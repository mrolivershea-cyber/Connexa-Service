import asyncio
import sys
import sqlite3
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test():
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_light" LIMIT 200')
    nodes = cursor.fetchall()
    conn.close()
    
    print(f'Testing {len(nodes)} nodes...\n')
    
    success_nodes = []
    
    for i, (ip, login, password) in enumerate(nodes, 1):
        login = login or 'admin'
        password = password or 'admin'
        
        try:
            result = await asyncio.wait_for(
                PPTPAuthenticator.authentic_pptp_test(ip, login, password, timeout=10.0),
                timeout=12.0
            )
            
            if result.get('success'):
                success_nodes.append((ip, login, password, result.get('avg_time')))
                print(f'{i}/200 SUCCESS: {ip} - {result.get("avg_time")}ms')
            
            if i % 20 == 0:
                print(f'Progress: {i}/200, found {len(success_nodes)} working')
                
        except:
            pass
    
    print(f'\n{"=" * 80}')
    print(f'TOTAL: {len(success_nodes)} working nodes out of 200')
    print(f'Success rate: {len(success_nodes)*100/200:.1f}%')
    print(f'{"=" * 80}')
    
    if success_nodes:
        print('\nFIRST 10 WORKING NODES:')
        for ip, login, password, ping_ms in success_nodes[:10]:
            print(f'  {ip} ({login}:{password}) - {ping_ms}ms')

asyncio.run(test())
