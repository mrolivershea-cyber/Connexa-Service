#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class SpeedAlgorithmTester:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def make_request(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text, "status_code": response.status_code}

            return success, response_data

        except Exception as e:
            return False, {"error": str(e)}

    def test_login(self):
        """Test login with admin credentials"""
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log_test("Admin Login", True)
            return True
        else:
            self.log_test("Admin Login", False, f"Login failed: {response}")
            return False

    def test_single_speed_test_real_data(self):
        """ТЕСТ 1: Проверка единичного speed теста с реальными данными"""
        print(f"\n🔍 ТЕСТ 1: Единичный Speed Test - Реальные данные")
        
        # Получить узлы со статусом ping_ok
        nodes_success, nodes_response = self.make_request('GET', 'nodes?status=ping_ok&limit=5')
        
        if not nodes_success or not nodes_response.get('nodes'):
            self.log_test("Single Speed Test - Get ping_ok nodes", False, 
                         "❌ Не найдены узлы со статусом ping_ok для тестирования")
            return False
        
        ping_ok_nodes = nodes_response['nodes']
        if len(ping_ok_nodes) == 0:
            self.log_test("Single Speed Test - Get ping_ok nodes", False, 
                         "❌ В базе нет узлов со статусом ping_ok")
            return False
        
        # Выбрать первый узел для тестирования
        test_node = ping_ok_nodes[0]
        node_id = test_node['id']
        node_ip = test_node['ip']
        
        print(f"📍 Тестируем узел: ID={node_id}, IP={node_ip}")
        
        # Запустить speed test через POST /api/manual/speed-test-batch-progress
        speed_data = {
            "node_ids": [node_id]
        }
        
        speed_success, speed_response = self.make_request('POST', 'manual/speed-test-batch-progress', speed_data)
        
        if speed_success and 'session_id' in speed_response:
            session_id = speed_response['session_id']
            
            # Мониторить прогресс
            max_wait = 60  # Максимум 60 секунд ожидания
            wait_time = 0
            
            while wait_time < max_wait:
                progress_success, progress_response = self.make_request('GET', f'progress/{session_id}')
                
                if progress_success:
                    status = progress_response.get('status', 'unknown')
                    
                    if status == 'completed':
                        results = progress_response.get('results', [])
                        
                        if results and len(results) > 0:
                            result = results[0]
                            
                            # Проверить что результат содержит реальные данные
                            download_mbps = result.get('download_mbps', 0)
                            upload_mbps = result.get('upload_mbps', 0)
                            ping_ms = result.get('ping_ms', 0)
                            method = result.get('method', '')
                            
                            # Проверить что метод = "real_tcp_throughput_measurement"
                            if method == "real_tcp_throughput_measurement":
                                self.log_test("Single Speed Test - Real Method", True, 
                                             f"✅ Метод корректный: {method}")
                            else:
                                self.log_test("Single Speed Test - Real Method", False, 
                                             f"❌ Неправильный метод: {method} (ожидался real_tcp_throughput_measurement)")
                            
                            # Проверить что данные реальные (не все нули)
                            if download_mbps > 0 or upload_mbps > 0:
                                self.log_test("Single Speed Test - Real Data", True, 
                                             f"✅ Реальные данные: download={download_mbps} Mbps, upload={upload_mbps} Mbps, ping={ping_ms} ms")
                            else:
                                self.log_test("Single Speed Test - Real Data", False, 
                                             f"❌ Подозрительные данные (все нули): download={download_mbps}, upload={upload_mbps}")
                            
                            # Проверить что статус узла обновился на speed_ok
                            node_check_success, node_check_response = self.make_request('GET', f'nodes/{node_id}')
                            if node_check_success:
                                final_status = node_check_response.get('status')
                                if final_status == 'speed_ok':
                                    self.log_test("Single Speed Test - Status Update", True, 
                                                 f"✅ Статус узла корректно обновлен на speed_ok")
                                else:
                                    self.log_test("Single Speed Test - Status Update", False, 
                                                 f"❌ Статус узла не обновлен: {final_status} (ожидался speed_ok)")
                            
                            return True
                        else:
                            self.log_test("Single Speed Test - Results", False, 
                                         "❌ Нет результатов в ответе")
                            return False
                    
                    elif status == 'failed':
                        self.log_test("Single Speed Test - Execution", False, 
                                     f"❌ Speed test завершился с ошибкой: {progress_response}")
                        return False
                
                time.sleep(2)
                wait_time += 2
            
            self.log_test("Single Speed Test - Timeout", False, 
                         f"❌ Speed test не завершился за {max_wait} секунд")
            return False
        
        else:
            self.log_test("Single Speed Test - Start", False, 
                         f"❌ Не удалось запустить speed test: {speed_response}")
            return False

    def test_batch_speed_testing(self):
        """ТЕСТ 2: Проверка batch speed testing с 5 узлами"""
        print(f"\n🔍 ТЕСТ 2: Batch Speed Testing - 5 узлов")
        
        # Получить 5 узлов со статусом ping_ok
        nodes_success, nodes_response = self.make_request('GET', 'nodes?status=ping_ok&limit=5')
        
        if not nodes_success or not nodes_response.get('nodes'):
            self.log_test("Batch Speed Test - Get ping_ok nodes", False, 
                         "❌ Не найдены узлы со статусом ping_ok для batch тестирования")
            return False
        
        ping_ok_nodes = nodes_response['nodes']
        if len(ping_ok_nodes) < 5:
            self.log_test("Batch Speed Test - Insufficient nodes", False, 
                         f"❌ Недостаточно узлов для batch тестирования: найдено {len(ping_ok_nodes)}, нужно 5")
            return False
        
        # Взять первые 5 узлов
        test_nodes = ping_ok_nodes[:5]
        node_ids = [node['id'] for node in test_nodes]
        
        print(f"📍 Тестируем batch из {len(node_ids)} узлов: {node_ids}")
        
        # Запустить batch speed test
        batch_data = {
            "node_ids": node_ids
        }
        
        batch_success, batch_response = self.make_request('POST', 'manual/speed-test-batch-progress', batch_data)
        
        if batch_success and 'session_id' in batch_response:
            session_id = batch_response['session_id']
            
            # Мониторить прогресс
            max_wait = 180  # Максимум 3 минуты для batch теста
            wait_time = 0
            
            while wait_time < max_wait:
                progress_success, progress_response = self.make_request('GET', f'progress/{session_id}')
                
                if progress_success:
                    status = progress_response.get('status', 'unknown')
                    processed = progress_response.get('processed_items', 0)
                    total = progress_response.get('total_items', 0)
                    
                    print(f"📊 Прогресс: {processed}/{total}, статус: {status}")
                    
                    if status == 'completed':
                        results = progress_response.get('results', [])
                        
                        if len(results) >= 5:
                            # Проверить что система НЕ ЗАВИСАЕТ
                            self.log_test("Batch Speed Test - No Hanging", True, 
                                         f"✅ Система не зависла, batch test завершился успешно")
                            
                            # Проверить что результаты реалистичные (не все одинаковые скорости)
                            speeds = []
                            for result in results:
                                download = result.get('download_mbps', 0)
                                upload = result.get('upload_mbps', 0)
                                speeds.append((download, upload))
                            
                            # Проверить разнообразие скоростей
                            unique_downloads = set([s[0] for s in speeds])
                            unique_uploads = set([s[1] for s in speeds])
                            
                            if len(unique_downloads) > 1 or len(unique_uploads) > 1:
                                self.log_test("Batch Speed Test - Realistic Results", True, 
                                             f"✅ Результаты реалистичные: разные скорости между узлами")
                            else:
                                self.log_test("Batch Speed Test - Realistic Results", False, 
                                             f"❌ Подозрительно одинаковые скорости: {speeds}")
                            
                            return True
                        else:
                            self.log_test("Batch Speed Test - Results Count", False, 
                                         f"❌ Недостаточно результатов: {len(results)} из 5")
                            return False
                    
                    elif status == 'failed':
                        self.log_test("Batch Speed Test - Execution", False, 
                                     f"❌ Batch speed test завершился с ошибкой")
                        return False
                
                time.sleep(5)
                wait_time += 5
            
            self.log_test("Batch Speed Test - Timeout", False, 
                         f"❌ Batch speed test не завершился за {max_wait} секунд")
            return False
        
        else:
            self.log_test("Batch Speed Test - Start", False, 
                         f"❌ Не удалось запустить batch speed test: {batch_response}")
            return False

    def test_backend_logs_verification(self):
        """ТЕСТ 3: Проверка логов backend"""
        print(f"\n🔍 ТЕСТ 3: Проверка Backend Логов")
        
        # Проверить логи backend через supervisor
        try:
            import subprocess
            
            # Получить последние 100 строк логов backend
            result = subprocess.run(
                ['tail', '-n', '100', '/var/log/supervisor/backend.out.log'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                log_content = result.stdout
                
                # Проверить что ВСЕ успешные тесты логируются как "✅ speed success"
                success_logs = [line for line in log_content.split('\n') if '✅ speed success' in line]
                failed_logs = [line for line in log_content.split('\n') if '❌ speed failed' in line]
                
                if success_logs:
                    self.log_test("Backend Logs - Success Logging", True, 
                                 f"✅ Найдены логи успешных speed тестов: {len(success_logs)} записей")
                else:
                    self.log_test("Backend Logs - Success Logging", False, 
                                 "❌ Не найдены логи успешных speed тестов")
                
                # Проверить что в логах НЕТ сообщений с "connection_based_estimate"
                estimate_logs = [line for line in log_content.split('\n') if 'connection_based_estimate' in line]
                
                if not estimate_logs:
                    self.log_test("Backend Logs - No Fake Method", True, 
                                 f"✅ В логах НЕТ упоминаний connection_based_estimate")
                else:
                    self.log_test("Backend Logs - No Fake Method", False, 
                                 f"❌ Найдены упоминания connection_based_estimate в логах: {len(estimate_logs)}")
                
                return True
            
            else:
                self.log_test("Backend Logs - Access", False, 
                             f"❌ Не удалось получить логи backend: {result.stderr}")
                return False
        
        except Exception as e:
            self.log_test("Backend Logs - Access", False, 
                         f"❌ Ошибка при проверке логов: {str(e)}")
            return False

    def run_speed_algorithm_fix_tests(self):
        """КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ: Проверка исправлений SPEED OK алгоритма"""
        print(f"\n🔥 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ SPEED OK АЛГОРИТМА - НАЧАЛО")
        
        # ТЕСТ 1: Проверка единичного speed теста
        self.test_single_speed_test_real_data()
        
        # ТЕСТ 2: Проверка batch speed testing
        self.test_batch_speed_testing()
        
        # ТЕСТ 3: Проверка логов backend
        self.test_backend_logs_verification()
        
        print(f"\n✅ КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ SPEED OK АЛГОРИТМА - ЗАВЕРШЕНО")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔥 КРИТИЧЕСКОЕ ТЕСТИРОВАНИЕ SPEED OK АЛГОРИТМА")
    print("="*80)
    
    tester = SpeedAlgorithmTester()
    
    # Login first
    if not tester.test_login():
        print("❌ Login failed - cannot run tests")
        sys.exit(1)
    
    # Run the SPEED OK algorithm fix tests
    tester.run_speed_algorithm_fix_tests()
    
    # Print summary
    print(f"\n📊 SPEED OK ALGORITHM FIX TESTS SUMMARY:")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("✅ ALL SPEED OK ALGORITHM FIX TESTS PASSED")
    else:
        print("❌ SOME SPEED OK ALGORITHM FIX TESTS FAILED")
        failed_tests = [r for r in tester.test_results if not r['success']]
        for test in failed_tests:
            print(f"   ❌ {test['test']}: {test['details']}")