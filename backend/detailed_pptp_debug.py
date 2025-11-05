import asyncio
import sqlite3
import sys
import struct
import time
sys.path.insert(0, '/app/backend')

async def debug_pptp(ip, login, password):
    """Детальная отладка PPTP соединения"""
    print(f'\n{"=" * 80}')
    print(f'ДЕТАЛЬНАЯ ОТЛАДКА: {ip} ({login}:{password})')
    print('=' * 80)
    
    try:
        # Шаг 1: TCP соединение
        print('\n[ШАГ 1] Подключение к TCP порту 1723...')
        start = time.time()
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, 1723),
            timeout=5.0
        )
        connect_time = (time.time() - start) * 1000
        print(f'  ✅ TCP подключение успешно за {connect_time:.1f}ms')
        
        # Шаг 2: Отправка Start-Request
        print('\n[ШАГ 2] Отправка PPTP Start-Request...')
        start_request = struct.pack('>HH', 156, 1)
        start_request += struct.pack('>L', 0x1a2b3c4d)
        start_request += struct.pack('>HH', 1, 0)
        start_request += struct.pack('>HH', 1, 0)
        start_request += struct.pack('>L', 1)
        start_request += struct.pack('>L', 1)
        start_request += struct.pack('>HH', 1, 1)
        hostname = b'PPTP_CLIENT'
        start_request += hostname + (b'\x00' * (64 - len(hostname)))
        vendor = b'PPTP_VENDOR'
        start_request += vendor + (b'\x00' * (64 - len(vendor)))
        
        writer.write(start_request)
        await asyncio.wait_for(writer.drain(), timeout=2.0)
        print(f'  ✅ Start-Request отправлен ({len(start_request)} bytes)')
        
        # Шаг 3: Чтение Start-Reply
        print('\n[ШАГ 3] Чтение Start-Reply...')
        response = await asyncio.wait_for(reader.read(1024), timeout=5.0)
        print(f'  ✅ Получен ответ ({len(response)} bytes)')
        
        if len(response) >= 21:
            length, msg_type = struct.unpack('>HH', response[:4])
            magic = struct.unpack('>L', response[4:8])[0]
            control_type = struct.unpack('>H', response[8:10])[0]
            result_code = struct.unpack('>B', response[20:21])[0]
            
            print(f'  Length: {length}')
            print(f'  Message Type: {msg_type}')
            print(f'  Magic Cookie: {hex(magic)}')
            print(f'  Control Type: {control_type} (2=Start-Reply)')
            print(f'  Result Code: {result_code} (1=Success)')
            
            if result_code != 1:
                print(f'  ⚠️ Result code {result_code} но продолжаем...')
        
        # Шаг 4: Outgoing Call Request
        print('\n[ШАГ 4] Отправка Outgoing Call Request...')
        call_request = struct.pack('>HH', 168, 1)
        call_request += struct.pack('>L', 0x1a2b3c4d)
        call_request += struct.pack('>HH', 7, 0)
        call_request += struct.pack('>HH', 1, 2)
        call_request += struct.pack('>L', 300)
        call_request += struct.pack('>L', 100000000)
        call_request += struct.pack('>L', 1)
        call_request += struct.pack('>L', 1)
        call_request += struct.pack('>HH', 1500, 64)
        call_request += struct.pack('>HH', len(login), 0)
        phone_field = login.encode()[:64]
        call_request += phone_field + (b'\x00' * (64 - len(phone_field)))
        subaddr_field = b'PPTP_SUBADDR'[:64]
        call_request += subaddr_field + (b'\x00' * (64 - len(subaddr_field)))
        
        writer.write(call_request)
        await asyncio.wait_for(writer.drain(), timeout=2.0)
        print(f'  ✅ Call Request отправлен ({len(call_request)} bytes)')
        
        # Шаг 5: Call-Reply
        print('\n[ШАГ 5] Чтение Outgoing Call-Reply...')
        call_response = await asyncio.wait_for(reader.read(1024), timeout=5.0)
        print(f'  ✅ Получен ответ ({len(call_response)} bytes)')
        
        if len(call_response) >= 21:
            call_result = struct.unpack('>B', call_response[20:21])[0]
            print(f'  Call Result: {call_result}')
            print(f'    0 = Success (no error)')
            print(f'    1 = Connected')
            print(f'    2 = General error')
            print(f'    3 = No carrier')
            print(f'    4 = Busy')
            print(f'    5 = No dial tone')
            
            if call_result <= 1:
                print(f'  ✅ SUCCESS! Call result {call_result}')
                return True
            else:
                print(f'  ❌ FAILED! Call result {call_result}')
                
                # Показываем hex dump
                print(f'\n  HEX DUMP Call-Reply (first 50 bytes):')
                hex_str = ' '.join(f'{b:02x}' for b in call_response[:50])
                print(f'  {hex_str}')
                return False
        
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f'\n  ❌ ОШИБКА: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

async def main():
    # Берем несколько узлов ping_light которые не прошли тест
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ip, login, password FROM nodes WHERE status = "ping_light" LIMIT 3')
    nodes = cursor.fetchall()
    conn.close()
    
    print('ДЕТАЛЬНАЯ ОТЛАДКА PPTP НА 3 УЗЛАХ')
    
    for ip, login, password in nodes:
        login = login or 'admin'
        password = password or 'admin'
        await debug_pptp(ip, login, password)

asyncio.run(main())
