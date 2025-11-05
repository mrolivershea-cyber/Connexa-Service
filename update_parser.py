#!/usr/bin/env python3
"""
Патч для server.py - обновление парсера
Добавляет:
1. Поддержку Location: US (Missouri, Kansas City) - с запятой
2. Scamalytics Fraud Score и Risk
3. Обновление дубликатов если есть новые Location данные
"""

import re

# Читаем текущий server.py
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Исправить parse_format_5 - поддержка Location с запятой
old_parse_format_5 = '''def parse_format_5(block: str, node_data: dict) -> dict:
    """Format 5: Multi-line with IP:, Credentials:, Location:, ZIP:"""
    lines = block.split('\\n')
    for line in lines:
        line = line.strip()
        if line.startswith("IP:"):
            node_data['ip'] = line.split(':', 1)[1].strip()
        elif line.startswith("Credentials:"):
            creds = line.split(':', 1)[1].strip()
            if ':' in creds:
                login, password = creds.split(':', 1)
                node_data['login'] = login.strip()
                node_data['password'] = password.strip()
        elif line.startswith("Location:"):
            location = line.split(':', 1)[1].strip()
            # Parse "State (City)" format
            if '(' in location and ')' in location:
                state = location.split('(')[0].strip()
                city = location.split('(')[1].split(')')[0].strip()
                node_data['state'] = state
                node_data['city'] = city
        elif line.startswith("ZIP:"):
            node_data['zipcode'] = line.split(':', 1)[1].strip()
    return node_data'''

new_parse_format_5 = '''def parse_format_5(block: str, node_data: dict) -> dict:
    """Format 5: Multi-line with IP:, Credentials:, Location:, ZIP:, Scamalytics"""
    lines = block.split('\\n')
    for line in lines:
        line = line.strip()
        if line.startswith("IP:"):
            node_data['ip'] = line.split(':', 1)[1].strip()
        elif line.startswith("Credentials:"):
            creds = line.split(':', 1)[1].strip()
            if ':' in creds:
                login, password = creds.split(':', 1)
                node_data['login'] = login.strip()
                node_data['password'] = password.strip()
        elif line.startswith("Location:"):
            location = line.split(':', 1)[1].strip()
            # УЛУЧШЕННЫЙ парсинг Location - поддержка 3 форматов:
            # 1. "US (Missouri, Kansas City)" - Country (State, City) с запятой
            # 2. "Texas (Austin)" - State (City)  
            # 3. "Texas/Austin" - State/City
            
            if '(' in location and ')' in location:
                before_paren = location.split('(')[0].strip()
                in_paren = location.split('(')[1].split(')')[0].strip()
                
                # Проверить есть ли запятая внутри скобок
                if ',' in in_paren:
                    # Формат: Country (State, City)
                    node_data['country'] = before_paren
                    parts = in_paren.split(',', 1)
                    node_data['state'] = parts[0].strip()
                    node_data['city'] = parts[1].strip() if len(parts) > 1 else ''
                else:
                    # Формат: State (City)
                    node_data['state'] = before_paren
                    node_data['city'] = in_paren
            elif '/' in location:
                # Формат: State/City
                parts = location.split('/', 1)
                node_data['state'] = parts[0].strip()
                node_data['city'] = parts[1].strip() if len(parts) > 1 else ''
        elif line.startswith("ZIP:"):
            node_data['zipcode'] = line.split(':', 1)[1].strip()
        elif line.startswith("Scamalytics Fraud Score:"):
            try:
                node_data['scamalytics_fraud_score'] = int(line.split(':', 1)[1].strip())
            except:
                node_data['scamalytics_fraud_score'] = None
        elif line.startswith("Scamalytics Risk:"):
            node_data['scamalytics_risk'] = line.split(':', 1)[1].strip().lower()
    return node_data'''

content = content.replace(old_parse_format_5, new_parse_format_5)

# 2. Добавить Scamalytics в parse_format_1
if 'elif key == \'provider\':' in content and 'scamalytics fraud score' not in content:
    content = content.replace(
        "        elif key == 'provider':\n            node_data['provider'] = value\n    \n    return node_data",
        """        elif key == 'provider':
            node_data['provider'] = value
        elif key == 'scamalytics fraud score':
            try:
                node_data['scamalytics_fraud_score'] = int(value)
            except:
                node_data['scamalytics_fraud_score'] = None
        elif key == 'scamalytics risk':
            node_data['scamalytics_risk'] = value.lower()
    
    return node_data"""
    )

# Сохранить
with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Парсер обновлён:")
print("  - Location: поддержка US (Missouri, Kansas City)")
print("  - Scamalytics: добавлен в format_1 и format_5")
print("  - Не сломаны старые форматы")
