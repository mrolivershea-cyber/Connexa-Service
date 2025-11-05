#!/usr/bin/env python3
"""
Миграция для объединенной системы статусов
Исправляет статусы узлов которые на самом деле не тестировались
"""
import sqlite3
from datetime import datetime

def migrate_unified_status():
    conn = sqlite3.connect('backend/connexa.db')
    cursor = conn.cursor()
    
    print("🔄 Начинаю миграцию к объединенной системе статусов...")
    
    # 1. Удалить поле ping_status (создать новую таблицу без этого поля)
    print("1️⃣ Удаляю поле ping_status...")
    
    # Создать новую таблицу без ping_status
    cursor.execute('''
    CREATE TABLE nodes_new (
        id INTEGER PRIMARY KEY,
        ip VARCHAR(45) NOT NULL,
        port INTEGER,
        login VARCHAR(100),
        password VARCHAR(255),
        provider VARCHAR(100),
        country VARCHAR(100), 
        state VARCHAR(100),
        city VARCHAR(100),
        zipcode VARCHAR(20),
        comment TEXT,
        protocol VARCHAR(10),
        status VARCHAR(20) DEFAULT 'not_tested',
        speed VARCHAR(20),
        last_check DATETIME,
        last_update DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Скопировать данные (без ping_status)
    cursor.execute('''
    INSERT INTO nodes_new (id, ip, port, login, password, provider, country, state, city, zipcode, comment, protocol, status, speed, last_check, last_update, created_at)
    SELECT id, ip, port, login, password, provider, country, state, city, zipcode, comment, protocol, status, speed, last_check, last_update, created_at
    FROM nodes
    ''')
    
    # 2. Установить правильные статусы
    print("2️⃣ Устанавливаю правильные статусы...")
    
    # Узлы которые никогда не тестировались -> not_tested
    cursor.execute('''
    UPDATE nodes_new 
    SET status = 'not_tested', last_check = NULL
    WHERE last_check IS NULL AND status IN ('offline', 'checking')
    ''')
    
    # Узлы которые реально тестировались на PING и провалились -> ping_failed  
    cursor.execute('''
    UPDATE nodes_new 
    SET status = 'ping_failed'
    WHERE last_check IS NOT NULL AND status = 'offline'
    ''')
    
    # Узлы со статусом checking тоже -> not_tested (если не тестировались)
    cursor.execute('''
    UPDATE nodes_new 
    SET status = 'not_tested'
    WHERE status = 'checking'
    ''')
    
    # 3. Заменить таблицы
    print("3️⃣ Заменяю таблицы...")
    cursor.execute('DROP TABLE nodes')
    cursor.execute('ALTER TABLE nodes_new RENAME TO nodes')
    
    # 4. Показать результат
    cursor.execute('SELECT status, COUNT(*) FROM nodes GROUP BY status')
    statuses = cursor.fetchall()
    print("\n✅ Миграция завершена! Новые статусы:")
    for status, count in statuses:
        print(f'  {status}: {count}')
    
    conn.commit()
    conn.close()
    print("🎉 Миграция успешно завершена!")

if __name__ == "__main__":
    migrate_unified_status()