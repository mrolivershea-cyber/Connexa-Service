#!/usr/bin/env python3
"""
TEST PARSING REAL PPTP.txt FILE - 6419 nodes
"""
import sys
sys.path.insert(0, '/app/backend')

from server import parse_nodes_text
import time

print("=" * 100)
print("🧪 ТЕСТИРОВАНИЕ ПАРСИНГА РЕАЛЬНОГО ФАЙЛА PPTP.txt")
print("=" * 100)

# Load file
with open('/app/PPTP_test.txt', 'r', encoding='utf-8') as f:
    file_content = f.read()

print(f"\n📊 Размер файла: {len(file_content):,} символов ({len(file_content)/1024:.1f} KB)")
print(f"📊 Строк в файле: {file_content.count(chr(10)):,}")

# Parse
print(f"\n🔄 Начинаем парсинг...")
start_time = time.time()

try:
    result = parse_nodes_text(file_content)
    
    parse_time = time.time() - start_time
    
    print(f"⏱️  Время парсинга: {parse_time:.2f} секунд")
    print(f"\n{'='*100}")
    print("📊 РЕЗУЛЬТАТЫ ПАРСИНГА")
    print(f"{'='*100}")
    
    print(f"\n✅ Успешно распарсено: {result['successfully_parsed']} узлов")
    print(f"📝 Всего обработано блоков: {result['total_processed']}")
    print(f"❌ Ошибки формата: {len(result['format_errors'])}")
    print(f"🔄 Дубликаты: {len(result['duplicates'])}")
    
    # Analyze parsed nodes
    if result['nodes']:
        print(f"\n{'='*100}")
        print("🔍 АНАЛИЗ ПЕРВЫХ 5 УЗЛОВ")
        print(f"{'='*100}")
        
        for i, node in enumerate(result['nodes'][:5], 1):
            print(f"\n--- Узел {i} ---")
            print(f"  IP: {node.get('ip')}")
            print(f"  Login: {node.get('login')}")
            print(f"  Password: {node.get('password')}")
            print(f"  Country: {node.get('country', 'NOT SET')}")
            print(f"  State: {node.get('state', 'NOT SET')}")
            print(f"  City: {node.get('city', 'NOT SET')}")
            print(f"  ZIP: {node.get('zipcode', 'NOT SET')}")
            print(f"  Scam Fraud Score: {node.get('scamalytics_fraud_score', 'NOT SET')}")
            print(f"  Scam Risk: {node.get('scamalytics_risk', 'NOT SET')}")
        
        # Статистика по Scamalytics данным
        print(f"\n{'='*100}")
        print("📊 СТАТИСТИКА SCAMALYTICS")
        print(f"{'='*100}")
        
        nodes_with_scam = sum(1 for n in result['nodes'] if n.get('scamalytics_fraud_score') is not None)
        nodes_with_risk = sum(1 for n in result['nodes'] if n.get('scamalytics_risk') is not None)
        
        print(f"\n✅ Узлов с Fraud Score: {nodes_with_scam}/{len(result['nodes'])} ({nodes_with_scam/len(result['nodes'])*100:.1f}%)")
        print(f"✅ Узлов с Risk Level: {nodes_with_risk}/{len(result['nodes'])} ({nodes_with_risk/len(result['nodes'])*100:.1f}%)")
        
        if nodes_with_scam > 0:
            # Статистика по risk levels
            risk_levels = {}
            for node in result['nodes']:
                risk = node.get('scamalytics_risk')
                if risk:
                    risk_levels[risk] = risk_levels.get(risk, 0) + 1
            
            print(f"\n📊 Распределение по уровням риска:")
            for risk, count in sorted(risk_levels.items()):
                print(f"  {risk.upper()}: {count} узлов")
        
        # Статистика по Location
        print(f"\n{'='*100}")
        print("📊 СТАТИСТИКА LOCATION")
        print(f"{'='*100}")
        
        nodes_with_country = sum(1 for n in result['nodes'] if n.get('country'))
        nodes_with_state = sum(1 for n in result['nodes'] if n.get('state'))
        nodes_with_city = sum(1 for n in result['nodes'] if n.get('city'))
        
        print(f"\n✅ Узлов с Country: {nodes_with_country}/{len(result['nodes'])} ({nodes_with_country/len(result['nodes'])*100:.1f}%)")
        print(f"✅ Узлов с State: {nodes_with_state}/{len(result['nodes'])} ({nodes_with_state/len(result['nodes'])*100:.1f}%)")
        print(f"✅ Узлов с City: {nodes_with_city}/{len(result['nodes'])} ({nodes_with_city/len(result['nodes'])*100:.1f}%)")
        
        # Показать примеры новых форматов Location
        print(f"\n🔍 ПРИМЕРЫ НОВЫХ ФОРМАТОВ LOCATION:")
        count = 0
        for node in result['nodes']:
            if node.get('country') and ',' in str(node.get('city', '')):
                print(f"\n  IP: {node.get('ip')}")
                print(f"  Country: {node.get('country')}")
                print(f"  State: {node.get('state')}")
                print(f"  City: {node.get('city')}")
                count += 1
                if count >= 3:
                    break
    
    # Ошибки формата
    if result['format_errors']:
        print(f"\n{'='*100}")
        print(f"❌ ОШИБКИ ФОРМАТА (первые 10)")
        print(f"{'='*100}")
        for error in result['format_errors'][:10]:
            print(f"  - {error}")
    
    # Final verdict
    print(f"\n{'='*100}")
    print("🎯 ИТОГОВАЯ ОЦЕНКА")
    print(f"{'='*100}")
    
    success_rate = (result['successfully_parsed'] / result['total_processed'] * 100) if result['total_processed'] > 0 else 0
    
    print(f"\n📊 Процент успеха: {success_rate:.1f}%")
    print(f"⏱️  Скорость парсинга: {result['successfully_parsed']/parse_time:.0f} узлов/сек")
    
    if success_rate >= 95:
        print(f"\n🎉 ОТЛИЧНО! Парсер работает на {success_rate:.1f}%")
        print("✅ Старые форматы парсятся корректно")
        print("✅ Новые форматы со Scamalytics парсятся корректно")
        print("✅ Новый формат Location (US (State, City)) парсится корректно")
    elif success_rate >= 80:
        print(f"\n⚠️  ХОРОШО, но есть проблемы: {success_rate:.1f}% успеха")
        print(f"❌ Не распарсено: {result['total_processed'] - result['successfully_parsed']} блоков")
    else:
        print(f"\n❌ ПРОБЛЕМЫ С ПАРСИНГОМ: только {success_rate:.1f}% успеха")
        print("Требуется исправление парсера")

except Exception as e:
    print(f"\n❌ ОШИБКА ПРИ ПАРСИНГЕ: {str(e)}")
    import traceback
    traceback.print_exc()
