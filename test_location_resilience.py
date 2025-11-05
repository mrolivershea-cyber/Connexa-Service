#!/usr/bin/env python3
"""
COMPREHENSIVE Location parsing test - проверка УСТОЙЧИВОСТИ к изменениям формата
"""
import sys
sys.path.insert(0, '/app/backend')

from server import parse_location_smart

# Test cases для разных форматов Location
test_cases = [
    {
        "name": "Текущий формат: Country (State, City) - запятая в скобках",
        "input": "US (Washington, Mill Creek)",
        "expected": ("US", "Washington", "Mill Creek")
    },
    {
        "name": "Если уберут запятую → точка: Country (State. City)",
        "input": "US (Washington. Mill Creek)",
        "expected": ("US", "Washington", "Mill Creek")
    },
    {
        "name": "Если заменят на двоеточие: Country (State: City)",
        "input": "US (Washington: Mill Creek)",
        "expected": ("US", "Washington", "Mill Creek")
    },
    {
        "name": "Если уберут все разделители: Country (State  City) - двойной пробел",
        "input": "US (Washington  Mill Creek)",
        "expected": ("US", "Washington", "Mill Creek")
    },
    {
        "name": "Если уберут скобки но оставят запятую: Country, State, City",
        "input": "US, Washington, Mill Creek",
        "expected": ("US", "Washington", "Mill Creek")
    },
    {
        "name": "Если оставят только пробелы: Country State City",
        "input": "US Washington Mill Creek",
        "expected": ("US", "Washington", "Mill Creek")
    },
    {
        "name": "Без страны (State, City) - запятая",
        "input": "Washington, Mill Creek",
        "expected": (None, "Washington", "Mill Creek")
    },
    {
        "name": "Без страны State (City) - скобки",
        "input": "Texas (Austin)",
        "expected": (None, "Texas", "Austin")
    },
    {
        "name": "Без страны и скобок: State City - пробел",
        "input": "Washington Mill Creek",
        "expected": (None, "Washington", "Mill Creek")
    },
    {
        "name": "Город из нескольких слов: Country (State, Kansas City)",
        "input": "US (Missouri, Kansas City)",
        "expected": ("US", "Missouri", "Kansas City")
    },
    {
        "name": "Штат из нескольких слов: Country, New York, New York City",
        "input": "US, New York, New York City",
        "expected": ("US", "New York", "New York City")
    },
    {
        "name": "Точки везде: Country. State. City",
        "input": "US. Washington. Mill Creek",
        "expected": ("US", "Washington", "Mill Creek")
    },
    {
        "name": "Двоеточия везде: Country: State: City",
        "input": "US: Washington: Mill Creek",
        "expected": ("US", "Washington", "Mill Creek")
    },
    {
        "name": "Одинарный пробел внутри скобок: Country (State City)",
        "input": "US (Washington Mill Creek)",
        "expected": ("US", "Washington", "Mill Creek")
    },
]

print("=" * 100)
print("🧪 ТЕСТ УСТОЙЧИВОСТИ ПАРСЕРА LOCATION К ИЗМЕНЕНИЯМ ФОРМАТА")
print("=" * 100)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    result = parse_location_smart(test['input'])
    
    country = result['country']
    state = result['state']
    city = result['city']
    
    exp_country, exp_state, exp_city = test['expected']
    
    country_match = country == exp_country
    state_match = state == exp_state
    city_match = city == exp_city
    
    all_match = country_match and state_match and city_match
    
    status = "✅ PASSED" if all_match else "❌ FAILED"
    
    print(f"\n{'-'*100}")
    print(f"TEST {i}: {test['name']}")
    print(f"{'-'*100}")
    print(f"📍 Input: '{test['input']}'")
    print(f"\n📊 Expected → Got:")
    print(f"  Country: {str(exp_country):20} → {str(country):20} {'✅' if country_match else '❌'}")
    print(f"  State:   {str(exp_state):20} → {str(state):20} {'✅' if state_match else '❌'}")
    print(f"  City:    {str(exp_city):20} → {str(city):20} {'✅' if city_match else '❌'}")
    print(f"\n{status}")
    
    if all_match:
        passed += 1
    else:
        failed += 1

# Summary
print(f"\n{'='*100}")
print("📊 ИТОГОВАЯ СТАТИСТИКА")
print(f"{'='*100}")
print(f"\n✅ PASSED: {passed}/{len(test_cases)} tests ({passed/len(test_cases)*100:.1f}%)")
print(f"❌ FAILED: {failed}/{len(test_cases)} tests ({failed/len(test_cases)*100:.1f}%)")

if passed == len(test_cases):
    print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ!")
    print("\n✅ Парсер Location ПОЛНОСТЬЮ УСТОЙЧИВ к изменениям:")
    print("   - Работает если уберут скобки")
    print("   - Работает если заменят запятую на точку/двоеточие/пробелы")
    print("   - Работает если изменят количество пробелов")
    print("   - Работает с городами и штатами из нескольких слов")
    print("   - Работает с разными комбинациями Country/State/City")
    print("\n🛡️ ПАРСЕР ГОТОВ К ЛЮБЫМ ИЗМЕНЕНИЯМ ФОРМАТА!")
elif passed >= len(test_cases) * 0.9:
    print(f"\n⚠️ {failed} тестов не прошли, но {passed/len(test_cases)*100:.0f}% работает")
    print("Парсер устойчив к большинству изменений формата")
else:
    print(f"\n❌ Требуется доработка - только {passed/len(test_cases)*100:.0f}% тестов прошло")
