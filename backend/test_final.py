import asyncio
import sys
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test():
    # Тестируем известный рабочий узел
    ip = '24.227.222.163'
    login = 'admin'
    password = 'admin'
    
    print('Testing known working node...')
    result = await PPTPAuthenticator.authentic_pptp_test(ip, login, password)
    
    print(f'Result: {"SUCCESS" if result.get("success") else "FAILED"}')
    print(f'Message: {result.get("message")}')

asyncio.run(test())
