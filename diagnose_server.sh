#!/bin/bash
#
# 🔍 ДИАГНОСТИКА CONNEXA - Сбор данных для анализа
#

echo "================================================================================"
echo "🔍 CONNEXA DIAGNOSTIC REPORT"
echo "================================================================================"

# Определяем директорию
if [ -d "/opt/connexa" ]; then
    DIR="/opt/connexa"
elif [ -d "/app" ]; then
    DIR="/app"
else
    echo "❌ Директория не найдена"
    exit 1
fi

echo "📂 Директория: $DIR"
echo ""

# 1. Версия репозитория
echo "================================================================================"
echo "1️⃣ ВЕРСИЯ РЕПОЗИТОРИЯ"
echo "================================================================================"
cd $DIR
echo "Git URL:"
git config --get remote.origin.url
echo ""
echo "Последний коммит:"
git log -1 --oneline
echo ""
echo "Последнее обновление:"
git log -1 --format="%ai"
echo ""

# 2. Проверка ключевых функций в server.py
echo "================================================================================"
echo "2️⃣ ПРОВЕРКА КЛЮЧЕВЫХ ФУНКЦИЙ В BACKEND"
echo "================================================================================"

echo "Функция parse_location_smart существует:"
grep -c "def parse_location_smart" $DIR/backend/server.py || echo "❌ НЕТ"

echo "Функция использует приоритетные разделители:"
grep -A5 "if ',' in inside_bracket:" $DIR/backend/server.py | head -6 || echo "❌ Старая версия"

echo ""
echo "Параметры get_nodes включают speed_min:"
grep "speed_min: Optional" $DIR/backend/server.py || echo "❌ НЕТ"

echo ""
echo "apply_node_filters_kwargs обрабатывает speed_min:"
grep -A3 "if speed_min:" $DIR/backend/server.py | head -4 || echo "❌ НЕТ"

echo ""

# 3. Проверка Frontend импортов
echo "================================================================================"
echo "3️⃣ ПРОВЕРКА FRONTEND ИМПОРТОВ"
echo "================================================================================"

echo "AdminPanel.js импорты:"
head -15 $DIR/frontend/src/components/AdminPanel.js | grep "from.*components/ui" | head -3

echo ""
echo "NodesTable.js импорты:"
head -15 $DIR/frontend/src/components/NodesTable.js | grep "from.*components/ui" | head -3

echo ""

# 4. Тест парсинга на сервере
echo "================================================================================"
echo "4️⃣ ТЕСТ ПАРСИНГА НА СЕРВЕРЕ"
echo "================================================================================"

cd $DIR/backend

# Используем venv если есть
if [ -d "venv" ]; then
    PYTHON="venv/bin/python3"
else
    PYTHON="python3"
fi

$PYTHON << 'PYEOF'
import sys
sys.path.insert(0, '.')

try:
    from server import parse_nodes_text
    
    # Test Format 1
    test1 = """
Ip: 71.84.237.32
Login: admin
Pass: admin
State: California
City: Pasadena
Zip: 91101
"""
    
    result = parse_nodes_text(test1)
    
    if result['nodes'] and len(result['nodes']) > 0:
        node = result['nodes'][0]
        print("Format 1 парсинг:")
        print(f"  IP: {node.get('ip')}")
        print(f"  State: {node.get('state', 'NOT SET')}")
        print(f"  City: {node.get('city', 'NOT SET')}")
        print(f"  ZIP: {node.get('zipcode', 'NOT SET')}")
        
        if node.get('state') == 'California':
            print("  ✅ Format 1 РАБОТАЕТ")
        else:
            print("  ❌ Format 1 НЕ РАБОТАЕТ")
    else:
        print("❌ Парсинг не сработал")
        
    # Test Scamalytics
    test2 = """
IP: 192.168.1.1
Credentials: admin:pass
Location: US (Washington, Mill Creek)
ZIP: 98012
Scamalytics Fraud Score: 45
Scamalytics Risk: medium
"""
    
    result2 = parse_nodes_text(test2)
    
    if result2['nodes'] and len(result2['nodes']) > 0:
        node2 = result2['nodes'][0]
        print("")
        print("Format 5 + Scamalytics:")
        print(f"  Country: {node2.get('country', 'NOT SET')}")
        print(f"  State: {node2.get('state', 'NOT SET')}")
        print(f"  City: {node2.get('city', 'NOT SET')}")
        print(f"  Fraud: {node2.get('scamalytics_fraud_score', 'NOT SET')}")
        print(f"  Risk: {node2.get('scamalytics_risk', 'NOT SET')}")
        
        if node2.get('city') == 'Mill Creek' and node2.get('scamalytics_fraud_score') == 45:
            print("  ✅ Scamalytics РАБОТАЕТ")
        else:
            print("  ❌ Scamalytics НЕ РАБОТАЕТ")
        
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""

# 5. Данные из базы
echo "================================================================================"
echo "5️⃣ ДАННЫЕ ИЗ БАЗЫ"
echo "================================================================================"

$PYTHON << 'PYEOF'
import sqlite3

try:
    conn = sqlite3.connect('connexa.db')
    cursor = conn.cursor()
    
    # Статистика
    cursor.execute('SELECT COUNT(*) FROM nodes')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM nodes WHERE state IS NOT NULL AND state != ""')
    with_state = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM nodes WHERE scamalytics_fraud_score IS NOT NULL')
    with_scam = cursor.fetchone()[0]
    
    print(f"Всего узлов: {total}")
    print(f"Со State: {with_state} ({with_state/total*100:.1f}%)")
    print(f"С Scamalytics: {with_scam} ({with_scam/total*100:.1f}%)")
    
    # Первые 3 узла
    print("")
    print("Первые 3 узла:")
    cursor.execute('SELECT ip, state, city, zipcode FROM nodes LIMIT 3')
    for ip, state, city, zipcode in cursor.fetchall():
        print(f"  {ip}: State={state or 'EMPTY'}, City={city or 'EMPTY'}, ZIP={zipcode or 'EMPTY'}")
    
    conn.close()
except Exception as e:
    print(f"❌ Ошибка работы с БД: {e}")
PYEOF

echo ""

# 6. Логи импорта
echo "================================================================================"
echo "6️⃣ ПОСЛЕДНИЕ ЛОГИ BACKEND (импорт)"
echo "================================================================================"

if [ -f "/var/log/connexa-backend.out.log" ]; then
    grep -i "import\|parse\|format" /var/log/connexa-backend.out.log | tail -20
else
    echo "⚠️  Логи не найдены"
fi

echo ""
echo "================================================================================"
echo "✅ ДИАГНОСТИКА ЗАВЕРШЕНА"
echo "================================================================================"
echo ""
echo "Скопируйте ВСЁ что выше и отправьте для анализа"
echo ""
