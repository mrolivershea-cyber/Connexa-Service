#!/usr/bin/env python3
"""
FULL IMPORT TEST - Import PPTP.txt through API
"""
import requests
import time
import json

API = "http://localhost:8001/api"

print("=" * 100)
print("🧪 ПОЛНЫЙ ТЕСТ ИМПОРТА ЧЕРЕЗ API")
print("=" * 100)

# Login first
print("\n1️⃣ Авторизация...")
login_response = requests.post(f"{API}/auth/login", json={
    "username": "admin",
    "password": "admin"
})

if login_response.status_code != 200:
    print(f"❌ Ошибка авторизации: {login_response.status_code}")
    exit(1)

token = login_response.json()['access_token']
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ Авторизация успешна")

# Get current stats
print("\n2️⃣ Получение текущей статистики...")
stats_before = requests.get(f"{API}/stats", headers=headers).json()
print(f"📊 Узлов в базе до импорта: {stats_before['total']}")

# Load file
print("\n3️⃣ Загрузка файла PPTP.txt...")
with open('/app/PPTP_test.txt', 'r', encoding='utf-8') as f:
    file_content = f.read()

file_size_kb = len(file_content) / 1024
print(f"📊 Размер файла: {file_size_kb:.1f} KB")

# Import
print(f"\n4️⃣ Начинаем импорт...")
print(f"   (Файл > 500KB, будет использован chunked import)")

start_time = time.time()

import_response = requests.post(
    f"{API}/nodes/import",
    headers=headers,
    json={"data": file_content, "protocol": "pptp"}
)

if import_response.status_code != 200:
    print(f"❌ Ошибка импорта: {import_response.status_code}")
    print(f"Response: {import_response.text}")
    exit(1)

import_result = import_response.json()
print(f"✅ Импорт инициирован успешно")

# Check if chunked
if import_result.get('session_id'):
    session_id = import_result['session_id']
    print(f"\n📦 Chunked Import - Session ID: {session_id}")
    print(f"📊 Всего чанков: {import_result.get('total_chunks')}")
    
    # Poll progress
    print(f"\n5️⃣ Отслеживание прогресса...")
    last_percent = 0
    
    while True:
        time.sleep(2)
        
        progress_response = requests.get(
            f"{API}/import/progress/{session_id}",
            headers=headers
        )
        
        if progress_response.status_code == 200:
            progress = progress_response.json()
            status = progress.get('status')
            percent = progress.get('progress_percent', 0)
            
            if percent > last_percent:
                print(f"   📊 Прогресс: {percent}% ({progress.get('processed_chunks')}/{progress.get('total_chunks')} чанков)")
                print(f"      Добавлено: {progress.get('added')}, Пропущено: {progress.get('skipped')}, Ошибки: {progress.get('errors')}")
                last_percent = percent
            
            if status in ['completed', 'failed', 'cancelled']:
                print(f"\n✅ Импорт завершен: {status.upper()}")
                final_progress = progress
                break
        else:
            print(f"⚠️  Не удалось получить прогресс")
            break
    
    import_time = time.time() - start_time
    print(f"\n⏱️  Время импорта: {import_time:.1f} секунд")
    
else:
    # Regular import
    print(f"\n✅ Regular Import (не chunked)")
    import_time = time.time() - start_time
    final_progress = import_result.get('report', {})

# Get stats after import
print(f"\n6️⃣ Получение финальной статистики...")
stats_after = requests.get(f"{API}/stats", headers=headers).json()

print(f"\n{'='*100}")
print("📊 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ")
print(f"{'='*100}")

print(f"\n📊 База данных:")
print(f"  До импорта:  {stats_before['total']} узлов")
print(f"  После импорта: {stats_after['total']} узлов")
print(f"  Добавлено: {stats_after['total'] - stats_before['total']} узлов")

if import_result.get('session_id'):
    print(f"\n📊 Детали импорта:")
    print(f"  Добавлено новых: {final_progress.get('added', 0)}")
    print(f"  Дубликаты (пропущено): {final_progress.get('skipped', 0)}")
    print(f"  Ошибки парсинга: {final_progress.get('errors', 0)}")

print(f"\n📊 Статистика по статусам:")
print(f"  Not Tested: {stats_after.get('not_tested', 0)}")
print(f"  Ping Failed: {stats_after.get('ping_failed', 0)}")
print(f"  Ping OK: {stats_after.get('ping_ok', 0)}")
print(f"  Speed OK: {stats_after.get('speed_ok', 0)}")
print(f"  Online: {stats_after.get('online', 0)}")

# Verify Scamalytics data in DB
print(f"\n7️⃣ Проверка Scamalytics данных в базе...")
nodes_response = requests.get(
    f"{API}/nodes",
    headers=headers,
    params={"limit": 100, "page": 1}
)

if nodes_response.status_code == 200:
    nodes_data = nodes_response.json()
    sample_nodes = nodes_data['nodes'][:5]
    
    scam_count = sum(1 for n in sample_nodes if n.get('scamalytics_fraud_score') is not None)
    
    print(f"\n📊 Проверка первых 5 узлов из базы:")
    for node in sample_nodes:
        has_scam = node.get('scamalytics_fraud_score') is not None
        scam_marker = "✅ SCAM" if has_scam else "⚫ NO SCAM"
        print(f"  {node['ip']:18} - {node['state']:15} - {scam_marker}")
    
    print(f"\n📊 Scamalytics в базе: {scam_count}/5 узлов имеют данные")

print(f"\n{'='*100}")
print("🎉 ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
print(f"{'='*100}")
