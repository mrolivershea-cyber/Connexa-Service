#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class MassTestingSuite:
    def __init__(self, base_url="https://memory-mcp.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED - {details}")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def make_request(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response"""
        url = f"{self.api_url}/{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=60)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data, timeout=30)
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
            self.log_test("Admin Login", True, "Successfully logged in")
            return True
        else:
            self.log_test("Admin Login", False, f"Login failed: {response}")
            return False

    def test_mass_testing_step1_preparation(self):
        """Шаг 1: Подготовка - Select 50 nodes of different statuses"""
        print("\n" + "="*80)
        print("МАССОВОЕ ТЕСТИРОВАНИЕ - ШАГ 1: ПОДГОТОВКА (50 УЗЛОВ)")
        print("="*80 + "\n")
        
        # Get nodes from database with different statuses
        success, response = self.make_request('GET', 'nodes?limit=2000')
        
        if not success or 'nodes' not in response:
            self.log_test("Mass Testing Step 1 - Preparation", False, f"Failed to get nodes: {response}")
            return None
        
        all_nodes = response['nodes']
        
        # Categorize nodes by status
        nodes_by_status = {
            'not_tested': [],
            'ping_failed': [],
            'ping_light': [],
            'speed_ok': []
        }
        
        for node in all_nodes:
            status = node.get('status', '')
            if status in nodes_by_status:
                nodes_by_status[status].append(node)
        
        # Select 50 nodes: mix of different statuses
        # Priority: not_tested (10), ping_failed (10), ping_light (15), speed_ok (15)
        selected_nodes = []
        
        # Add not_tested nodes (up to 10)
        selected_nodes.extend(nodes_by_status['not_tested'][:10])
        
        # Add ping_failed nodes (up to 10)
        selected_nodes.extend(nodes_by_status['ping_failed'][:10])
        
        # Add ping_light nodes (up to 15)
        selected_nodes.extend(nodes_by_status['ping_light'][:15])
        
        # Add speed_ok nodes (up to 15)
        selected_nodes.extend(nodes_by_status['speed_ok'][:15])
        
        # If we don't have 50, fill with whatever is available
        if len(selected_nodes) < 50:
            remaining = 50 - len(selected_nodes)
            for status in ['ping_light', 'speed_ok', 'ping_failed', 'not_tested']:
                if remaining <= 0:
                    break
                available = [n for n in nodes_by_status[status] if n not in selected_nodes]
                selected_nodes.extend(available[:remaining])
                remaining = 50 - len(selected_nodes)
        
        # Limit to 50
        selected_nodes = selected_nodes[:50]
        
        if len(selected_nodes) >= 30:  # At least 30 nodes needed for testing
            status_counts = {}
            for node in selected_nodes:
                status = node.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            self.log_test("Mass Testing Step 1 - Preparation", True, 
                         f"Selected {len(selected_nodes)} nodes: {status_counts}")
            return selected_nodes
        else:
            self.log_test("Mass Testing Step 1 - Preparation", False, 
                         f"Only found {len(selected_nodes)} nodes, need at least 30")
            return None
    
    def test_mass_testing_step2_ping_light(self, selected_nodes):
        """Шаг 2: PING LIGHT тесты (30 узлов)"""
        print("\n" + "="*80)
        print("МАССОВОЕ ТЕСТИРОВАНИЕ - ШАГ 2: PING LIGHT ТЕСТЫ (30 УЗЛОВ)")
        print("="*80 + "\n")
        
        if not selected_nodes:
            self.log_test("Mass Testing Step 2 - PING LIGHT", False, "No nodes provided")
            return None
        
        # Select 30 nodes for PING LIGHT testing (prefer not_tested and ping_failed)
        ping_light_candidates = []
        for node in selected_nodes:
            status = node.get('status', '')
            if status in ['not_tested', 'ping_failed']:
                ping_light_candidates.append(node)
        
        # If not enough, add ping_light nodes
        if len(ping_light_candidates) < 30:
            for node in selected_nodes:
                if node not in ping_light_candidates and len(ping_light_candidates) < 30:
                    ping_light_candidates.append(node)
        
        ping_light_nodes = ping_light_candidates[:30]
        node_ids = [node['id'] for node in ping_light_nodes]
        
        print(f"Testing PING LIGHT on {len(node_ids)} nodes...")
        print(f"Node IDs: {node_ids[:10]}..." if len(node_ids) > 10 else f"Node IDs: {node_ids}")
        
        # Call manual ping-test-batch endpoint with PING LIGHT mode
        test_data = {
            "node_ids": node_ids,
            "mode": "ping_light"
        }
        
        success, response = self.make_request('POST', 'manual/ping-test-batch', test_data)
        
        if not success:
            self.log_test("Mass Testing Step 2 - PING LIGHT", False, f"API call failed: {response}")
            return None
        
        # Wait for tests to complete
        print("Waiting for PING LIGHT tests to complete (15 seconds)...")
        time.sleep(15)
        
        # Verify results
        successful_tests = 0
        nodes_with_city = 0
        nodes_with_state = 0
        nodes_with_zip = 0
        nodes_with_provider = 0
        status_changes = 0
        
        for node_id in node_ids:
            node_success, node_response = self.make_request('GET', f'nodes/{node_id}')
            
            if node_success:
                node = node_response
                
                # Check if status changed to ping_light
                if node.get('status') == 'ping_light':
                    status_changes += 1
                    successful_tests += 1
                
                # Check if geo data filled
                if node.get('city'):
                    nodes_with_city += 1
                if node.get('state'):
                    nodes_with_state += 1
                if node.get('zip') or node.get('zipcode'):
                    nodes_with_zip += 1
                if node.get('provider'):
                    nodes_with_provider += 1
        
        success_rate = (successful_tests / len(node_ids)) * 100 if node_ids else 0
        
        if successful_tests >= len(node_ids) * 0.3:  # At least 30% success
            self.log_test("Mass Testing Step 2 - PING LIGHT", True, 
                         f"PING LIGHT tests: {successful_tests}/{len(node_ids)} successful ({success_rate:.1f}%), "
                         f"City: {nodes_with_city}, State: {nodes_with_state}, ZIP: {nodes_with_zip}, "
                         f"Provider: {nodes_with_provider}, Status changes: {status_changes}")
            return ping_light_nodes
        else:
            self.log_test("Mass Testing Step 2 - PING LIGHT", False, 
                         f"PING LIGHT tests: {successful_tests}/{len(node_ids)} successful ({success_rate:.1f}%)")
            return None
    
    def test_mass_testing_step3_ping_ok(self, selected_nodes):
        """Шаг 3: PING OK тесты (20 узлов с ping_light статусом)"""
        print("\n" + "="*80)
        print("МАССОВОЕ ТЕСТИРОВАНИЕ - ШАГ 3: PING OK ТЕСТЫ (20 УЗЛОВ)")
        print("="*80 + "\n")
        
        if not selected_nodes:
            self.log_test("Mass Testing Step 3 - PING OK", False, "No nodes provided")
            return None
        
        # Get nodes with ping_light status
        success, response = self.make_request('GET', 'nodes?status=ping_light&limit=50')
        
        if not success or 'nodes' not in response:
            self.log_test("Mass Testing Step 3 - PING OK", False, f"Failed to get ping_light nodes: {response}")
            return None
        
        ping_light_nodes = response['nodes'][:20]
        node_ids = [node['id'] for node in ping_light_nodes]
        
        if len(node_ids) < 10:
            self.log_test("Mass Testing Step 3 - PING OK", False, 
                         f"Not enough ping_light nodes: {len(node_ids)}, need at least 10")
            return None
        
        print(f"Testing PING OK on {len(node_ids)} ping_light nodes...")
        print(f"Node IDs: {node_ids[:10]}..." if len(node_ids) > 10 else f"Node IDs: {node_ids}")
        
        # Call manual ping-test-batch endpoint with PING OK mode
        test_data = {
            "node_ids": node_ids,
            "mode": "ping"
        }
        
        success, response = self.make_request('POST', 'manual/ping-test-batch', test_data)
        
        if not success:
            self.log_test("Mass Testing Step 3 - PING OK", False, f"API call failed: {response}")
            return None
        
        # Wait for tests to complete
        print("Waiting for PING OK tests to complete (20 seconds)...")
        time.sleep(20)
        
        # Verify results
        successful_tests = 0
        nodes_with_fraud_score = 0
        nodes_with_risk_level = 0
        nodes_with_zip_fallback = 0
        status_changes = 0
        
        for node_id in node_ids:
            node_success, node_response = self.make_request('GET', f'nodes/{node_id}')
            
            if node_success:
                node = node_response
                
                # Check if status changed to ping_ok
                if node.get('status') == 'ping_ok':
                    status_changes += 1
                    successful_tests += 1
                
                # Check if IPQS data filled (enrich_node_complete)
                fraud_score = node.get('scamalytics_fraud_score')
                if fraud_score is not None and 0 <= fraud_score <= 100:
                    nodes_with_fraud_score += 1
                
                risk_level = node.get('scamalytics_risk')
                if risk_level in ['low', 'medium', 'high', 'critical']:
                    nodes_with_risk_level += 1
                
                # Check if ZIP filled via fallback
                if node.get('zip') or node.get('zipcode'):
                    nodes_with_zip_fallback += 1
        
        success_rate = (successful_tests / len(node_ids)) * 100 if node_ids else 0
        
        if successful_tests >= len(node_ids) * 0.2:  # At least 20% success (PPTP may fail)
            self.log_test("Mass Testing Step 3 - PING OK", True, 
                         f"PING OK tests: {successful_tests}/{len(node_ids)} successful ({success_rate:.1f}%), "
                         f"Fraud Score: {nodes_with_fraud_score}, Risk Level: {nodes_with_risk_level}, "
                         f"ZIP filled: {nodes_with_zip_fallback}, Status changes: {status_changes}")
            return ping_light_nodes
        else:
            self.log_test("Mass Testing Step 3 - PING OK", False, 
                         f"PING OK tests: {successful_tests}/{len(node_ids)} successful ({success_rate:.1f}%)")
            return None
    
    def test_mass_testing_step4_filters(self):
        """Шаг 4: Проверка фильтров"""
        print("\n" + "="*80)
        print("МАССОВОЕ ТЕСТИРОВАНИЕ - ШАГ 4: ПРОВЕРКА ФИЛЬТРОВ")
        print("="*80 + "\n")
        
        # Test 1: Speed filter (speed_min=10, speed_max=50)
        filters_speed = {
            "speed_min": 10,
            "speed_max": 50,
            "limit": 100
        }
        
        success1, response1 = self.make_request('GET', 'nodes', filters_speed)
        
        speed_filter_ok = False
        if success1 and 'nodes' in response1:
            nodes = response1['nodes']
            # Verify all nodes have speed between 10 and 50
            all_in_range = True
            for node in nodes:
                speed = node.get('speed')
                if speed:
                    try:
                        speed_val = float(speed)
                        if not (10 <= speed_val <= 50):
                            all_in_range = False
                            break
                    except:
                        pass
            
            if all_in_range or len(nodes) == 0:
                speed_filter_ok = True
                self.log_test("Mass Testing Step 4 - Speed Filter", True, 
                             f"Speed filter working: {len(nodes)} nodes with speed 10-50 Mbps")
            else:
                self.log_test("Mass Testing Step 4 - Speed Filter", False, 
                             f"Speed filter failed: found nodes outside range")
        else:
            self.log_test("Mass Testing Step 4 - Speed Filter", False, f"API call failed: {response1}")
        
        # Test 2: Fraud Score filter (scam_fraud_score_min=0, scam_fraud_score_max=50)
        filters_fraud = {
            "scam_fraud_score_min": 0,
            "scam_fraud_score_max": 50,
            "limit": 100
        }
        
        success2, response2 = self.make_request('GET', 'nodes', filters_fraud)
        
        fraud_filter_ok = False
        if success2 and 'nodes' in response2:
            nodes = response2['nodes']
            # Verify all nodes have fraud score between 0 and 50
            all_in_range = True
            for node in nodes:
                fraud_score = node.get('scamalytics_fraud_score')
                if fraud_score is not None:
                    if not (0 <= fraud_score <= 50):
                        all_in_range = False
                        break
            
            if all_in_range or len(nodes) == 0:
                fraud_filter_ok = True
                self.log_test("Mass Testing Step 4 - Fraud Score Filter", True, 
                             f"Fraud Score filter working: {len(nodes)} nodes with score 0-50")
            else:
                self.log_test("Mass Testing Step 4 - Fraud Score Filter", False, 
                             f"Fraud Score filter failed: found nodes outside range")
        else:
            self.log_test("Mass Testing Step 4 - Fraud Score Filter", False, f"API call failed: {response2}")
        
        # Test 3: Risk filter (scam_risk='low')
        filters_risk = {
            "scam_risk": "low",
            "limit": 100
        }
        
        success3, response3 = self.make_request('GET', 'nodes', filters_risk)
        
        risk_filter_ok = False
        if success3 and 'nodes' in response3:
            nodes = response3['nodes']
            # Verify all nodes have risk level 'low'
            all_low_risk = True
            for node in nodes:
                risk = node.get('scamalytics_risk')
                if risk and risk != 'low':
                    all_low_risk = False
                    break
            
            if all_low_risk or len(nodes) == 0:
                risk_filter_ok = True
                self.log_test("Mass Testing Step 4 - Risk Filter", True, 
                             f"Risk filter working: {len(nodes)} nodes with risk='low'")
            else:
                self.log_test("Mass Testing Step 4 - Risk Filter", False, 
                             f"Risk filter failed: found nodes with risk != 'low'")
        else:
            self.log_test("Mass Testing Step 4 - Risk Filter", False, f"API call failed: {response3}")
        
        return speed_filter_ok and fraud_filter_ok and risk_filter_ok
    
    def test_mass_testing_step5_database_verification(self):
        """Шаг 5: Проверка в БД"""
        print("\n" + "="*80)
        print("МАССОВОЕ ТЕСТИРОВАНИЕ - ШАГ 5: ПРОВЕРКА В БД")
        print("="*80 + "\n")
        
        # Get all nodes to check database state
        success, response = self.make_request('GET', 'nodes?limit=3000')
        
        if not success or 'nodes' not in response:
            self.log_test("Mass Testing Step 5 - Database Verification", False, f"Failed to get nodes: {response}")
            return False
        
        all_nodes = response['nodes']
        
        # Count nodes with filled City
        nodes_with_city = sum(1 for node in all_nodes if node.get('city'))
        
        # Count nodes with Fraud Score
        nodes_with_fraud_score = sum(1 for node in all_nodes if node.get('scamalytics_fraud_score') is not None)
        
        # Distribution of Risk levels
        risk_distribution = {}
        for node in all_nodes:
            risk = node.get('scamalytics_risk')
            if risk:
                risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        
        # Status distribution
        status_distribution = {}
        for node in all_nodes:
            status = node.get('status', 'unknown')
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        self.log_test("Mass Testing Step 5 - Database Verification", True, 
                     f"Database state: Total nodes: {len(all_nodes)}, "
                     f"Nodes with City: {nodes_with_city}, "
                     f"Nodes with Fraud Score: {nodes_with_fraud_score}, "
                     f"Risk distribution: {risk_distribution}, "
                     f"Status distribution: {status_distribution}")
        
        return True
    
    def check_backend_logs_for_errors(self):
        """Check backend logs for errors"""
        try:
            import subprocess
            result = subprocess.run(
                ['tail', '-n', '200', '/var/log/supervisor/backend.err.log'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.stdout
        except Exception as e:
            return f"Error checking logs: {str(e)}"
    
    def run_mass_testing_suite(self):
        """Run complete mass testing suite (50 nodes)"""
        print("\n" + "="*80)
        print("МАССОВОЕ ТЕСТИРОВАНИЕ 50 УЗЛОВ - Connexa Admin Panel")
        print("="*80 + "\n")
        
        # Login first
        if not self.test_login():
            print("\n❌ Login failed - cannot continue with mass testing")
            return
        
        # Step 1: Preparation
        selected_nodes = self.test_mass_testing_step1_preparation()
        
        if not selected_nodes:
            print("\n❌ Step 1 failed - cannot continue")
            return
        
        # Step 2: PING LIGHT tests (30 nodes)
        ping_light_results = self.test_mass_testing_step2_ping_light(selected_nodes)
        
        # Step 3: PING OK tests (20 nodes)
        ping_ok_results = self.test_mass_testing_step3_ping_ok(selected_nodes)
        
        # Step 4: Filter verification
        filters_ok = self.test_mass_testing_step4_filters()
        
        # Step 5: Database verification
        db_ok = self.test_mass_testing_step5_database_verification()
        
        # Check backend logs for errors
        print("\n" + "="*80)
        print("ПРОВЕРКА ЛОГОВ BACKEND")
        print("="*80 + "\n")
        
        logs = self.check_backend_logs_for_errors()
        if logs:
            print("Recent backend logs (last 200 lines):")
            print(logs[-3000:])  # Print last 3000 characters
        
        print("\n" + "="*80)
        print("МАССОВОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("="*80 + "\n")
        
        # Print summary
        print(f"\nTotal tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed / self.tests_run * 100):.1f}%\n")

if __name__ == "__main__":
    tester = MassTestingSuite()
    tester.run_mass_testing_suite()
