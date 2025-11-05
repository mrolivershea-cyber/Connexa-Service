import asyncio
import sys
sys.path.insert(0, '/app/backend')

from pptp_auth_test import PPTPAuthenticator

async def test():
    ip = '24.227.222.163'
    login = 'admin'
    password = 'admin'
    
    print('=' * 80)
    print(f'TESTING KNOWN WORKING NODE: {ip}')
    print('=' * 80)
    
    print(f'\nNode: {ip} ({login}:{password})')
    print('User says: THIS NODE DEFINITELY WORKS\n')
    
    try:
        result = await asyncio.wait_for(
            PPTPAuthenticator.authentic_pptp_test(ip, login, password, timeout=15.0),
            timeout=20.0
        )
        
        print(f'Result: {"SUCCESS" if result.get("success") else "FAILED"}')
        print(f'Message: {result.get("message")}')
        print(f'Auth tested: {result.get("auth_tested")}')
        print(f'Full result: {result}')
        
        if not result.get('success'):
            print('\n' + '=' * 80)
            print('ERROR: Node should work but test failed!')
            print('This means PPTP implementation has a bug')
            print('=' * 80)
        else:
            print('\n' + '=' * 80)
            print('SUCCESS: PPTP test working correctly!')
            print('=' * 80)
            
    except Exception as e:
        print(f'\nException: {str(e)}')
        import traceback
        traceback.print_exc()

asyncio.run(test())
