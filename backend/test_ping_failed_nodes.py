import asyncio
import sqlite3
import sys
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test():
    # Берем 20 узлов ping_failed
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_failed" LIMIT 20')
    nodes = cursor.fetchall()
    conn.close()
    
    print(f'=== ТЕСТИРОВАНИЕ {len(nodes)} УЗЛОВ PING_FAILED ===\n')
    
    working = []
    
    for ip, login, password in nodes:
        login = login or 'admin'
        password = password or 'admin'
        
        try:
            result = await asyncio.wait_for(
                PPTPAuthenticator.authentic_pptp_test(ip, login, password, timeout=8.0),
                timeout=10.0
            )
            
            if result.get('success'):
                working.append((ip, login, password))
                print(f'✅ WORKING: {ip} ({login}:{password})')
            else:
                print(f'❌ FAILED: {ip} - {result.get("message")[:50]}')
                
        except Exception as e:
            print(f'❌ ERROR: {ip} - {str(e)[:50]}')
    
    print(f'\n=== РЕЗУЛЬТАТ ===')
    print(f'Из {len(nodes)} узлов ping_failed:')
    print(f'✅ {len(working)} оказались РАБОЧИМИ!')
    print(f'❌ {len(nodes) - len(working)} действительно не работают')
    
    if working:
        print('\n⚠️ ЭТИ УЗЛЫ ДОЛЖНЫ БЫТЬ PING_OK:')
        for ip, login, password in working:
            print(f'  {ip} ({login}:{password})')

asyncio.run(test())
