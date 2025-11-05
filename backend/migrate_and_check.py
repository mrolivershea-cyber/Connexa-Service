#!/usr/bin/env python3
"""
Миграция БД + проверка всех модулей
"""
import sys
sys.path.insert(0, '/app/backend')

import sqlite3
from database import Base, engine

print("=== МИГРАЦИЯ БД ===")

# 1. Добавить колонки если их нет
conn = sqlite3.connect('/app/backend/connexa.db')
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

# 2. Проверить все модули
print("\n=== ПРОВЕРКА МОДУЛЕЙ ===")

try:
    from ip_geolocation import get_ip_geolocation
    print("✅ ip_geolocation")
except Exception as e:
    print(f"❌ ip_geolocation: {e}")

try:
    from ipapico_checker import ipapico_checker
    print("✅ ipapico_checker")
except Exception as e:
    print(f"❌ ipapico_checker: {e}")

try:
    from ipinfo_checker import ipinfo_checker
    print("✅ ipinfo_checker")
except Exception as e:
    print(f"❌ ipinfo_checker: {e}")

try:
    from ipqs_checker import ipqs_checker
    print("✅ ipqs_checker")
except Exception as e:
    print(f"❌ ipqs_checker: {e}")

try:
    from abuseipdb_checker import abuseipdb_checker
    print("✅ abuseipdb_checker")
except Exception as e:
    print(f"❌ abuseipdb_checker: {e}")

try:
    from maxmind_checker import maxmind_checker
    print("✅ maxmind_checker")
except Exception as e:
    print(f"❌ maxmind_checker: {e}")

try:
    from service_manager_geo import service_manager
    print("✅ service_manager_geo")
except Exception as e:
    print(f"❌ service_manager_geo: {e}")

# 3. Проверить server.py импортируется
try:
    from server import app
    print("✅ server.py импортируется")
except Exception as e:
    print(f"❌ server.py: {e}")

print("\n✅ МИГРАЦИЯ И ПРОВЕРКА ЗАВЕРШЕНЫ")
