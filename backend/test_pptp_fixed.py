import asyncio
import sys
sys.path.insert(0, '/app/backend')

from ping_speed_test import test_node_ping

async def test_fixed_pptp():
    print('=' * 80)
    print('TESTING FIXED PPTP PROTOCOL')
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
                test_node_ping(ip, login, password),
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
    print(f'TOTAL: {success_count} of 3 nodes passed PPTP auth')
    print('=' * 80)
    
    if success_count > 0:
        print('SUCCESS! PPTP protocol is working!')
    else:
        print('WARNING: Either credentials are wrong or protocol issue remains')

asyncio.run(test_fixed_pptp())
