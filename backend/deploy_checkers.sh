#!/bin/bash
# Скрипт для создания всех checker модулей на сервере
# Запустить: bash deploy_checkers.sh

cd /app/backend

echo "Создание checker модулей..."

# Скачать все файлы из текущей директории
for file in ipapico_checker.py ipinfo_checker.py maxmind_checker.py abuseipdb_checker.py service_manager_geo.py; do
    if [ -f "$file" ]; then
        echo "✅ $file уже существует"
    else
        echo "⚠️ $file отсутствует - создаётся"
        # Файл будет создан через git pull
    fi
done

# Миграция БД
echo ""
echo "Миграция БД..."
venv/bin/python3 << 'MIGRATE'
import sqlite3
conn = sqlite3.connect('connexa.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(nodes)")
columns = [col[1] for col in cursor.fetchall()]

if 'scamalytics_fraud_score' not in columns:
    cursor.execute('ALTER TABLE nodes ADD COLUMN scamalytics_fraud_score INTEGER DEFAULT NULL')
    print("✅ Добавлена scamalytics_fraud_score")
else:
    print("✅ scamalytics_fraud_score уже есть")

if 'scamalytics_risk' not in columns:
    cursor.execute('ALTER TABLE nodes ADD COLUMN scamalytics_risk TEXT DEFAULT NULL')
    print("✅ Добавлена scamalytics_risk")
else:
    print("✅ scamalytics_risk уже есть")

conn.commit()
conn.close()
MIGRATE

# Проверка модулей
echo ""
echo "Проверка модулей..."
venv/bin/python3 migrate_and_check.py

echo ""
echo "✅ Готово! Перезапусти backend: sudo supervisorctl restart backend"
