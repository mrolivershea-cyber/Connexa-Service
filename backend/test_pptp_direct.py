import asyncio
import sys
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test_pptp():
    print('=' * 80)
    print('TESTING PPTP - DIRECT FROM pptp_auth_test.py')
    print('=' * 80)
    
    test_nodes = [
        ('144.229.29.35', 'admin', 'admin'),
        ('76.178.64.46', 'admin', 'admin'),
        ('68.227.241.4', 'admin', 'admin'),
    ]
    
    success_count = 0
    
    for ip, login, password in test_nodes:
        print(f'\nNode: {ip} ({login}:{password})')
        try:
            result = await asyncio.wait_for(
                PPTPAuthenticator.authentic_pptp_test(ip, login, password),
                timeout=12.0
            )
            status = 'SUCCESS' if result.get('success') else 'FAILED'
            print(f'   Result: {status}')
            print(f'   Message: {result.get("message")}')
            
            if result.get('success'):
                success_count += 1
        except Exception as e:
            print(f'   Error: {str(e)}')
    
    print('\n' + '=' * 80)
    print(f'TOTAL: {success_count} of 3 nodes passed')
    print('=' * 80)

asyncio.run(test_pptp())
