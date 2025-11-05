import asyncio
import sqlite3
import sys
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def verify():
    # Берем 10 узлов которые остались ping_light
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_light" LIMIT 10')
    nodes = cursor.fetchall()
    conn.close()
    
    print('=== ПРОВЕРКА: Действительно ли узлы ping_light НЕ работают? ===\n')
    
    false_negatives = []
    
    for ip, login, password in nodes:
        login = login or 'admin'
        password = password or 'admin'
        
        try:
            result = await asyncio.wait_for(
                PPTPAuthenticator.authentic_pptp_test(ip, login, password, timeout=10.0),
                timeout=12.0
            )
            
            if result.get('success'):
                false_negatives.append((ip, login, password))
                print(f'❌ FALSE NEGATIVE: {ip} ({login}:{password}) - SHOULD BE ping_ok but marked ping_light!')
            else:
                print(f'✅ CORRECT: {ip} - really failed, message: {result.get("message")}')
                
        except Exception as e:
            print(f'✅ CORRECT: {ip} - exception: {str(e)[:50]}')
    
    print(f'\n=== РЕЗУЛЬТАТ ===')
    print(f'False negatives (неправильно помечены): {len(false_negatives)}')
    
    if false_negatives:
        print('\nУЗЛЫ КОТОРЫЕ ДОЛЖНЫ БЫТЬ ping_ok:')
        for ip, login, password in false_negatives:
            print(f'  {ip} ({login}:{password})')

asyncio.run(verify())
