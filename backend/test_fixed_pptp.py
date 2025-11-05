import asyncio
import sqlite3
import sys
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test():
    # Тестируем те же 3 узла
    test_nodes = [
        ('144.229.29.35', 'admin', 'admin'),
        ('76.178.64.46', 'admin', 'admin'),
        ('68.227.241.4', 'admin', 'admin'),
    ]
    
    print('ТЕСТИРОВАНИЕ С ИСПРАВЛЕННОЙ ПРОВЕРКОЙ call_result')
    print('=' * 80)
    
    success = 0
    for ip, login, password in test_nodes:
        result = await PPTPAuthenticator.authentic_pptp_test(ip, login, password)
        
        if result.get('success'):
            print(f'✅ {ip}: {result.get("message")}')
            success += 1
        else:
            print(f'❌ {ip}: {result.get("message")}')
    
    print(f'\n{"=" * 80}')
    print(f'SUCCESS: {success}/3')
    
    if success == 3:
        print('✅ ВСЕ 3 УЗЛА ПРОШЛИ! Теперь тестируем 50 узлов...')
        
        # Тестируем 50 узлов
        conn = sqlite3.connect('connexa.db')
        cursor = conn.cursor()
        cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_light" LIMIT 50')
        nodes = cursor.fetchall()
        conn.close()
        
        success_50 = 0
        for ip, login, password in nodes:
            login = login or 'admin'
            password = password or 'admin'
            
            try:
                result = await asyncio.wait_for(
                    PPTPAuthenticator.authentic_pptp_test(ip, login, password, timeout=8.0),
                    timeout=10.0
                )
                if result.get('success'):
                    success_50 += 1
            except:
                pass
        
        print(f'\nРЕЗУЛЬТАТ НА 50 УЗЛАХ: {success_50}/50 ({success_50*100/50:.0f}%)')
        print(f'Ожидаемо на 1529 узлах: ~{int(1529 * success_50 / 50)} узлов')

asyncio.run(test())
