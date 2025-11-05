#!/usr/bin/env python3
"""
Глубокий анализ PPTP авторизации для выяснения причин пропусков
Тестирует разные credentials и PPTP методы
"""

import asyncio
import socket
import struct
import time
from typing import Dict, List

# Популярные комбинации логин/пароль для PPTP
CREDENTIALS_TO_TEST = [
    ("admin", "admin"),
    ("admin", "password"),
    ("admin", "1234"),
    ("admin", ""),
    ("root", "root"),
    ("user", "user"),
    ("vpn", "vpn"),
    ("test", "test"),
]

class DeepPPTPTester:
    """Детальный тестер PPTP с логированием всех этапов"""
    
    @staticmethod
    async def test_pptp_detailed(ip: str, login: str, password: str, timeout: float = 15.0) -> Dict:
        """
        Детальный PPTP тест с логированием каждого этапа
        """
        result = {
            "ip": ip,
            "login": login,
            "password": password,
            "stages": {},
            "success": False,
            "failure_reason": None,
            "raw_responses": []
        }
        
        start_time = time.time()
        
        try:
            # ЭТАП 1: TCP Connection
            stage1_start = time.time()
            try:
                future = asyncio.open_connection(ip, 1723)
                reader, writer = await asyncio.wait_for(future, timeout=5.0)
                result["stages"]["tcp_connection"] = {
                    "success": True,
                    "time_ms": round((time.time() - stage1_start) * 1000, 1)
                }
            except asyncio.TimeoutError:
                result["stages"]["tcp_connection"] = {
                    "success": False,
                    "error": "Connection timeout"
                }
                result["failure_reason"] = "TCP_CONNECTION_TIMEOUT"
                return result
            except Exception as e:
                result["stages"]["tcp_connection"] = {
                    "success": False,
                    "error": str(e)
                }
                result["failure_reason"] = f"TCP_CONNECTION_ERROR: {str(e)}"
                return result
            
            # ЭТАП 2: PPTP Start-Request
            stage2_start = time.time()
            start_request = struct.pack('>HH', 156, 1)
            start_request += struct.pack('>L', 0x1a2b3c4d)
            start_request += struct.pack('>HH', 1, 0)
            start_request += struct.pack('>HH', 1, 0)
            start_request += struct.pack('>L', 1)
            start_request += struct.pack('>L', 1)
            start_request += struct.pack('>HH', 1, 1)
            start_request += b'PPTP_CLIENT' + b'\x00' * (64 - len('PPTP_CLIENT'))
            start_request += b'PPTP_VENDOR' + b'\x00' * (64 - len('PPTP_VENDOR'))
            
            writer.write(start_request)
            await writer.drain()
            
            result["stages"]["start_request_sent"] = {
                "success": True,
                "time_ms": round((time.time() - stage2_start) * 1000, 1),
                "packet_size": len(start_request)
            }
            
            # ЭТАП 3: Start-Reply
            stage3_start = time.time()
            try:
                response_data = await asyncio.wait_for(reader.read(1024), timeout=10.0)
                result["raw_responses"].append({
                    "stage": "start_reply",
                    "length": len(response_data),
                    "hex": response_data[:32].hex()
                })
                
                if len(response_data) < 16:
                    result["stages"]["start_reply"] = {
                        "success": False,
                        "error": f"Response too short: {len(response_data)} bytes"
                    }
                    result["failure_reason"] = "START_REPLY_TOO_SHORT"
                    writer.close()
                    return result
                
                # Парсим ответ
                length, msg_type = struct.unpack('>HH', response_data[:4])
                magic = struct.unpack('>L', response_data[4:8])[0]
                control_type = struct.unpack('>H', response_data[8:10])[0]
                result_code = struct.unpack('>B', response_data[20:21])[0] if len(response_data) > 20 else 0
                
                result["stages"]["start_reply"] = {
                    "success": True,
                    "time_ms": round((time.time() - stage3_start) * 1000, 1),
                    "length": length,
                    "msg_type": msg_type,
                    "magic": hex(magic),
                    "control_type": control_type,
                    "result_code": result_code
                }
                
                # Проверяем magic cookie
                if magic != 0x1a2b3c4d:
                    result["failure_reason"] = f"INVALID_MAGIC_COOKIE: {hex(magic)}"
                    writer.close()
                    return result
                
                # Проверяем control_type
                if control_type != 2:
                    result["failure_reason"] = f"UNEXPECTED_CONTROL_TYPE: {control_type} (expected 2)"
                    writer.close()
                    return result
                
            except asyncio.TimeoutError:
                result["stages"]["start_reply"] = {
                    "success": False,
                    "error": "Timeout waiting for Start-Reply"
                }
                result["failure_reason"] = "START_REPLY_TIMEOUT"
                writer.close()
                return result
            
            # ЭТАП 4: Outgoing-Call-Request (с credentials)
            stage4_start = time.time()
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
            call_request += login.encode()[:64].ljust(64, b'\x00')
            call_request += b'PPTP_SUBADDR'[:64].ljust(64, b'\x00')
            
            writer.write(call_request)
            await writer.drain()
            
            result["stages"]["call_request_sent"] = {
                "success": True,
                "time_ms": round((time.time() - stage4_start) * 1000, 1),
                "packet_size": len(call_request),
                "login_used": login
            }
            
            # ЭТАП 5: Outgoing-Call-Reply
            stage5_start = time.time()
            try:
                call_response = await asyncio.wait_for(reader.read(1024), timeout=10.0)
                result["raw_responses"].append({
                    "stage": "call_reply",
                    "length": len(call_response),
                    "hex": call_response[:32].hex()
                })
                
                if len(call_response) >= 20:
                    call_result = struct.unpack('>B', call_response[20:21])[0]
                    call_length = struct.unpack('>HH', call_response[:4])[0]
                    call_control = struct.unpack('>H', call_response[8:10])[0]
                    
                    result["stages"]["call_reply"] = {
                        "success": True,
                        "time_ms": round((time.time() - stage5_start) * 1000, 1),
                        "call_result": call_result,
                        "call_control": call_control,
                        "length": call_length
                    }
                    
                    # Анализ call_result
                    if call_result <= 5:
                        result["success"] = True
                        result["failure_reason"] = None
                    else:
                        result["failure_reason"] = f"CALL_REJECTED: call_result={call_result}"
                        
                        # Детальная классификация ошибок
                        error_codes = {
                            6: "AUTHENTICATION_FAILED",
                            7: "PROTOCOL_ERROR",
                            8: "CALL_DISCONNECTED",
                            9: "HARDWARE_ERROR"
                        }
                        result["error_classification"] = error_codes.get(call_result, "UNKNOWN_ERROR")
                else:
                    result["stages"]["call_reply"] = {
                        "success": False,
                        "error": f"Response too short: {len(call_response)} bytes"
                    }
                    result["failure_reason"] = "CALL_REPLY_TOO_SHORT"
                    
            except asyncio.TimeoutError:
                result["stages"]["call_reply"] = {
                    "success": False,
                    "error": "Timeout waiting for Call-Reply"
                }
                result["failure_reason"] = "CALL_REPLY_TIMEOUT"
            
            writer.close()
            await writer.wait_closed()
            
        except Exception as e:
            result["failure_reason"] = f"EXCEPTION: {str(e)}"
        
        result["total_time_ms"] = round((time.time() - start_time) * 1000, 1)
        return result

async def test_ip_with_multiple_credentials(ip: str) -> Dict:
    """
    Тестирует один IP с множественными credentials
    """
    print(f"\n{'='*80}")
    print(f"🔬 ДЕТАЛЬНОЕ ТЕСТИРОВАНИЕ: {ip}")
    print(f"{'='*80}\n")
    
    results = []
    
    for login, password in CREDENTIALS_TO_TEST:
        print(f"  Тестирую {login}:{password}...", end=" ")
        result = await DeepPPTPTester.test_pptp_detailed(ip, login, password)
        results.append(result)
        
        if result["success"]:
            print(f"✅ SUCCESS")
            break
        else:
            print(f"❌ FAILED - {result['failure_reason']}")
            # Пауза между попытками для защиты от bruteforce
            await asyncio.sleep(2)
    
    return {
        "ip": ip,
        "tested_credentials": len(results),
        "results": results,
        "any_success": any(r["success"] for r in results)
    }

async def main():
    """Главная функция тестирования"""
    print("🚀 ГЛУБОКИЙ АНАЛИЗ PPTP АВТОРИЗАЦИИ")
    print("="*80)
    
    # Читаем IP из файла
    try:
        with open('/tmp/test_ping_light_ips.txt', 'r') as f:
            ips = [line.strip() for line in f if line.strip()]
    except:
        print("❌ Не найден файл с IP адресами")
        return
    
    print(f"📋 Будет протестировано {len(ips)} IP адресов")
    print(f"🔑 Каждый IP тестируется с {len(CREDENTIALS_TO_TEST)} комбинациями credentials")
    print(f"⏱️  Пауза между попытками: 2 секунды (защита от bruteforce)")
    print()
    
    all_results = []
    for ip in ips:
        result = await test_ip_with_multiple_credentials(ip)
        all_results.append(result)
    
    # Анализ результатов
    print(f"\n{'='*80}")
    print("📊 ИТОГОВЫЙ АНАЛИЗ")
    print(f"{'='*80}\n")
    
    total_ips = len(all_results)
    successful_ips = sum(1 for r in all_results if r["any_success"])
    
    print(f"Total IP tested: {total_ips}")
    print(f"Successful authorizations: {successful_ips}")
    print(f"Failed authorizations: {total_ips - successful_ips}")
    print()
    
    # Анализ причин неудач
    failure_reasons = {}
    for result in all_results:
        if not result["any_success"]:
            for test in result["results"]:
                reason = test["failure_reason"]
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
    
    if failure_reasons:
        print("🔍 ПРИЧИНЫ НЕУДАЧ (частота):")
        for reason, count in sorted(failure_reasons.items(), key=lambda x: -x[1]):
            print(f"  {reason}: {count}")
    
    # Детальные результаты для каждого IP
    print(f"\n{'='*80}")
    print("📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ")
    print(f"{'='*80}\n")
    
    for result in all_results:
        ip = result["ip"]
        success = result["any_success"]
        
        if success:
            # Найти успешный тест
            successful_test = next(r for r in result["results"] if r["success"])
            print(f"✅ {ip}")
            print(f"   Credentials: {successful_test['login']}:{successful_test['password']}")
            print(f"   Total time: {successful_test['total_time_ms']}ms")
        else:
            print(f"❌ {ip}")
            # Показать первую неудачную попытку (admin:admin)
            first_test = result["results"][0]
            print(f"   Failure reason: {first_test['failure_reason']}")
            
            # Показать на каком этапе упало
            stages = first_test["stages"]
            failed_stage = None
            for stage_name, stage_data in stages.items():
                if not stage_data.get("success", True):
                    failed_stage = stage_name
                    break
            
            if failed_stage:
                print(f"   Failed at stage: {failed_stage}")
                print(f"   Stage error: {stages[failed_stage].get('error', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(main())
