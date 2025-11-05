#!/usr/bin/env python3
"""
Comprehensive Location parsing test - все возможные вариации
"""
import sys
sys.path.insert(0, '/app/backend')

from server import parse_nodes_text

# Test cases для разных форматов Location
test_cases = [
    {
        "name": "Format 1: Country (State, City) - с запятой",
        "data": """
IP: 192.168.1.1
Credentials: admin:pass
Location: US (Washington, Mill Creek)
ZIP: 98012
""",
        "expected": {"country": "US", "state": "Washington", "city": "Mill Creek"}
    },
    {
        "name": "Format 2: Country (State. City) - с точкой",
        "data": """
IP: 192.168.1.2
Credentials: admin:pass
Location: US (Washington. Mill Creek)
ZIP: 98012
""",
        "expected": {"country": "US", "state": "Washington", "city": "Mill Creek"}
    },
    {
        "name": "Format 3: Country (State: City) - с двоеточием",
        "data": """
IP: 192.168.1.3
Credentials: admin:pass
Location: US (Washington: Mill Creek)
ZIP: 98012
""",
        "expected": {"country": "US", "state": "Washington", "city": "Mill Creek"}
    },
    {
        "name": "Format 4: State (City) - без страны",
        "data": """
IP: 192.168.1.4
Credentials: admin:pass
Location: Texas (Austin)
ZIP: 78701
""",
        "expected": {"country": None, "state": "Texas", "city": "Austin"}
    },
    {
        "name": "Format 5: Country, State, City - запятые без скобок",
        "data": """
IP: 192.168.1.5
Credentials: admin:pass
Location: US, Washington, Mill Creek
ZIP: 98012
""",
        "expected": {"country": "US", "state": "Washington", "city": "Mill Creek"}
    },
    {
        "name": "Format 6: State, City - запятые без страны",
        "data": """
IP: 192.168.1.6
Credentials: admin:pass
Location: Washington, Mill Creek
ZIP: 98012
""",
        "expected": {"country": None, "state": "Washington", "city": "Mill Creek"}
    },
    {
        "name": "Format 7: Country State City - только пробелы",
        "data": """
IP: 192.168.1.7
Credentials: admin:pass
Location: US Washington Mill Creek
ZIP: 98012
""",
        "expected": {"country": "US", "state": "Washington", "city": "Mill Creek"}
    },
    {
        "name": "Format 8: State City - только пробелы без страны",
        "data": """
IP: 192.168.1.8
Credentials: admin:pass
Location: Washington Mill Creek
ZIP: 98012
""",
        "expected": {"country": None, "state": "Washington", "city": "Mill Creek"}
    },
    {
        "name": "Format 9: Country. State. City - точки",
        "data": """
IP: 192.168.1.9
Credentials: admin:pass
Location: US. Washington. Mill Creek
ZIP: 98012
""",
        "expected": {"country": "US", "state": "Washington", "city": "Mill Creek"}
    },
    {
        "name": "Format 10: Country (State  City) - двойной пробел",
        "data": """
IP: 192.168.1.10
Credentials: admin:pass
Location: US (Washington  Mill Creek)
ZIP: 98012
""",
        "expected": {"country": "US", "state": "Washington", "city": "Mill Creek"}
    },
    {
        "name": "Format 11: Multi-word city - Kansas City",
        "data": """
IP: 192.168.1.11
Credentials: admin:pass
Location: US (Missouri, Kansas City)
ZIP: 64101
""",
        "expected": {"country": "US", "state": "Missouri", "city": "Kansas City"}
    },
    {
        "name": "Format 12: Multi-word state - New York City",
        "data": """
IP: 192.168.1.12
Credentials: admin:pass
Location: US, New York, New York City
ZIP: 10001
""",
        "expected": {"country": "US", "state": "New York", "city": "New York City"}
    }
]

print("=" * 100)
print("COMPREHENSIVE LOCATION PARSING TEST - ВСЕ ВАРИАЦИИ")
print("=" * 100)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*100}")
    print(f"TEST {i}: {test['name']}")
    print(f"{'='*100}")
    
    result = parse_nodes_text(test['data'])
    
    if result['nodes'] and len(result['nodes']) > 0:
        node = result['nodes'][0]
        
        # Проверяем результаты
        country_match = node.get('country') == test['expected']['country']
        state_match = node.get('state') == test['expected']['state']
        city_match = node.get('city') == test['expected']['city']
        
        all_match = country_match and state_match and city_match
        
        # Выводим результаты
        print(f"📍 Входные данные: {test['data'].strip().split('Location:')[1].split('ZIP:')[0].strip()}")
        print(f"\n📊 Ожидаемый результат:")
        print(f"  Country: {test['expected']['country']}")
        print(f"  State:   {test['expected']['state']}")
        print(f"  City:    {test['expected']['city']}")
        
        print(f"\n📊 Полученный результат:")
        print(f"  Country: {node.get('country')} {'✅' if country_match else '❌'}")
        print(f"  State:   {node.get('state')} {'✅' if state_match else '❌'}")
        print(f"  City:    {node.get('city')} {'✅' if city_match else '❌'}")
        
        if all_match:
            print(f"\n✅ TEST {i}: PASSED")
            passed += 1
        else:
            print(f"\n❌ TEST {i}: FAILED")
            failed += 1
    else:
        print(f"❌ TEST {i}: FAILED - No nodes parsed")
        failed += 1

# Summary
print(f"\n{'='*100}")
print("FINAL SUMMARY")
print(f"{'='*100}")
print(f"\n✅ PASSED: {passed}/{len(test_cases)} tests")
print(f"❌ FAILED: {failed}/{len(test_cases)} tests")
print(f"\n📊 Success Rate: {(passed/len(test_cases)*100):.1f}%")

if passed == len(test_cases):
    print("\n🎉 ALL LOCATION PARSING TESTS PASSED!")
    print("✅ Парсер Location готов к любым изменениям формата!")
    print("✅ Работает с: скобками, запятыми, точками, двоеточиями, пробелами")
    print("✅ Поддерживает: Country (State, City), State (City), State City, и все комбинации")
else:
    print(f"\n⚠️ {failed} тестов не прошли - требуется дополнительная доработка")
