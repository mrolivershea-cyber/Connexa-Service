#!/usr/bin/env python3
"""
SOCKS Start/Stop Service Buttons Integration Tests
Testing the integration between AdminPanel buttons and SOCKS API endpoints
"""

import sys
sys.path.insert(0, '/app')

from backend_test import ConnexaAPITester

def main():
    print("="*80)
    print("🔥 SOCKS START/STOP SERVICE BUTTONS INTEGRATION TESTING")
    print("="*80)
    print("\nТЕСТОВЫЕ СЦЕНАРИИ:")
    print("СЦЕНАРИЙ 1: Запуск SOCKS на узле с ping_light статусом")
    print("СЦЕНАРИЙ 2: Запуск SOCKS на узле с speed_ok статусом")
    print("СЦЕНАРИЙ 3: Попытка запуска SOCKS на узле с неподходящим статусом")
    print("СЦЕНАРИЙ 4: Остановка SOCKS и возврат в ping_ok")
    print("СЦЕНАРИЙ 5: PPTP проверка при запуске (backend logs)")
    print("СЦЕНАРИЙ 6: Проверка автогенерации credentials")
    print("ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ:")
    print("- Проверка работы с Select All режимом (filters)")
    print("- Проверка что previous_status корректно сохраняется")
    print("="*80)
    print()
    
    tester = ConnexaAPITester()
    
    # Login first
    print("🔐 Logging in...")
    if not tester.test_login():
        print("❌ Login failed - cannot proceed with tests")
        return False
    
    print("\n" + "="*80)
    print("STARTING SOCKS INTEGRATION TESTS")
    print("="*80 + "\n")
    
    # Run SOCKS tests
    print("\n📋 СЦЕНАРИЙ 1: Запуск SOCKS на узле с ping_light статусом")
    print("-" * 80)
    tester.test_socks_start_on_ping_light_node()
    
    print("\n📋 СЦЕНАРИЙ 2: Запуск SOCKS на узле с speed_ok статусом")
    print("-" * 80)
    tester.test_socks_start_on_speed_ok_node()
    
    print("\n📋 СЦЕНАРИЙ 3: Попытка запуска SOCKS на узле с неподходящим статусом")
    print("-" * 80)
    tester.test_socks_start_on_invalid_status_node()
    
    print("\n📋 СЦЕНАРИЙ 4: Остановка SOCKS и возврат в ping_ok")
    print("-" * 80)
    tester.test_socks_stop_and_return_to_ping_ok()
    
    print("\n📋 СЦЕНАРИЙ 6: Проверка автогенерации credentials")
    print("-" * 80)
    tester.test_socks_credentials_autogeneration()
    
    print("\n📋 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Select All режим (filters)")
    print("-" * 80)
    tester.test_socks_select_all_mode()
    
    print("\n📋 ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: previous_status сохранение")
    print("-" * 80)
    tester.test_socks_previous_status_preservation()
    
    # Print summary
    print("\n" + "="*80)
    print(f"TEST SUMMARY: {tester.tests_passed}/{tester.tests_run} tests passed")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    print("="*80)
    
    return tester.tests_passed == tester.tests_run

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
