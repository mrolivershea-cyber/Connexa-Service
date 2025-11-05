#!/usr/bin/env python3
"""
Migration: Add missing columns to nodes table
"""
import sqlite3
import sys

DB_PATH = "/app/backend/connexa.db"

print("=" * 100)
print("🔧 DATABASE MIGRATION - Adding missing columns")
print("=" * 100)

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(nodes)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    print(f"\n📊 Существующих колонок: {len(existing_columns)}")
    
    # Columns to add
    columns_to_add = [
        ("previous_status", "VARCHAR(20)"),
        ("ppp_interface", "VARCHAR(20)"),
    ]
    
    added_count = 0
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            print(f"\n➕ Добавление колонки: {col_name} ({col_type})")
            try:
                cursor.execute(f"ALTER TABLE nodes ADD COLUMN {col_name} {col_type}")
                added_count += 1
                print(f"   ✅ Колонка {col_name} добавлена")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"   ⚠️  Колонка {col_name} уже существует")
                else:
                    print(f"   ❌ Ошибка: {e}")
        else:
            print(f"✅ Колонка {col_name} уже существует")
    
    conn.commit()
    
    # Verify
    cursor.execute("PRAGMA table_info(nodes)")
    final_columns = [row[1] for row in cursor.fetchall()]
    
    print(f"\n{'='*100}")
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*100}")
    print(f"\n✅ Было колонок: {len(existing_columns)}")
    print(f"➕ Добавлено: {added_count}")
    print(f"✅ Стало колонок: {len(final_columns)}")
    
    # Проверяем наличие ключевых колонок
    required_cols = ['scamalytics_fraud_score', 'scamalytics_risk', 'previous_status', 'ppp_interface']
    print(f"\n🔍 Проверка критичных колонок:")
    for col in required_cols:
        status = "✅" if col in final_columns else "❌"
        print(f"  {status} {col}")
    
    conn.close()
    
    print(f"\n{'='*100}")
    print("🎉 МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print(f"{'='*100}")
    
except Exception as e:
    print(f"\n❌ ОШИБКА МИГРАЦИИ: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
