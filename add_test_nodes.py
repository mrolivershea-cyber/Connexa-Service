#!/usr/bin/env python3
"""
Добавить тестовые узлы для демонстрации объединенной системы статусов
"""
import sqlite3
from datetime import datetime

def add_test_nodes():
    conn = sqlite3.connect('backend/connexa.db')
    cursor = conn.cursor()
    
    print("🔄 Добавляю тестовые узлы для демонстрации...")
    
    # Узлы для демонстрации всех статусов
    test_nodes = [
        # Not tested nodes
        ('192.168.1.10', 'admin', 'pass1', 'TestProvider', 'USA', 'CA', 'Los Angeles', '90210', 'Test node 1', 'pptp', 'not_tested', None, None),
        ('192.168.1.11', 'admin', 'pass2', 'TestProvider', 'USA', 'NY', 'New York', '10001', 'Test node 2', 'pptp', 'not_tested', None, None),
        ('192.168.1.12', 'admin', 'pass3', 'TestProvider', 'USA', 'TX', 'Houston', '77001', 'Test node 3', 'ssh', 'not_tested', None, None),
        
        # Ping failed nodes
        ('192.168.1.20', 'admin', 'pass4', 'TestProvider', 'UK', 'England', 'London', 'W1A', 'Failed ping node 1', 'pptp', 'ping_failed', datetime.now(), None),
        ('192.168.1.21', 'admin', 'pass5', 'TestProvider', 'UK', 'England', 'Manchester', 'M1', 'Failed ping node 2', 'ssh', 'ping_failed', datetime.now(), None),
        
        # Ping OK nodes
        ('192.168.1.30', 'admin', 'pass6', 'TestProvider', 'Germany', 'Bavaria', 'Munich', '80331', 'Ping OK node 1', 'pptp', 'ping_ok', datetime.now(), None),
        ('192.168.1.31', 'admin', 'pass7', 'TestProvider', 'Germany', 'Berlin', 'Berlin', '10115', 'Ping OK node 2', 'socks', 'ping_ok', datetime.now(), None),
        
        # Speed slow nodes
        ('192.168.1.40', 'admin', 'pass8', 'TestProvider', 'France', 'Paris', 'Paris', '75001', 'Slow speed node', 'pptp', 'speed_slow', datetime.now(), '0.8'),
        
        # Speed OK nodes  
        ('192.168.1.50', 'admin', 'pass9', 'TestProvider', 'Netherlands', 'North Holland', 'Amsterdam', '1012', 'Good speed node 1', 'pptp', 'speed_ok', datetime.now(), '5.2'),
        ('192.168.1.51', 'admin', 'pass10', 'TestProvider', 'Netherlands', 'South Holland', 'Rotterdam', '3011', 'Good speed node 2', 'ssh', 'speed_ok', datetime.now(), '12.1'),
        
        # Offline nodes
        ('192.168.1.60', 'admin', 'pass11', 'TestProvider', 'Japan', 'Tokyo', 'Tokyo', '100-0001', 'Offline node', 'pptp', 'offline', datetime.now(), '3.5'),
        
        # Online nodes
        ('192.168.1.70', 'admin', 'pass12', 'TestProvider', 'Singapore', 'Singapore', 'Singapore', '018956', 'Online node 1', 'pptp', 'online', datetime.now(), '8.9'),
        ('192.168.1.71', 'admin', 'pass13', 'TestProvider', 'Australia', 'NSW', 'Sydney', '2000', 'Online node 2', 'socks', 'online', datetime.now(), '15.3'),
    ]
    
    for node in test_nodes:
        cursor.execute('''
        INSERT INTO nodes (ip, login, password, provider, country, state, city, zipcode, comment, protocol, status, last_check, speed, port, last_update, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (*node, 1194))  # Default port
    
    conn.commit()
    
    # Показать результат
    cursor.execute('SELECT status, COUNT(*) FROM nodes GROUP BY status ORDER BY COUNT(*) DESC')
    statuses = cursor.fetchall()
    print("\n✅ Тестовые узлы добавлены! Статусы:")
    for status, count in statuses:
        print(f'  {status}: {count}')
    
    total = sum(count for _, count in statuses)
    print(f'\nВсего узлов: {total}')
    
    conn.close()
    print("🎉 Демонстрационная база готова!")

if __name__ == "__main__":
    add_test_nodes()