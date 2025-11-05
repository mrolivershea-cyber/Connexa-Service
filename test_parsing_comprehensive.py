#!/usr/bin/env python3
"""
Comprehensive test for all parsing formats including new Scamalytics fields
"""
import sys
import os
sys.path.insert(0, '/app/backend')

from server import parse_nodes_text, detect_format

# Test Format 5 with Scamalytics (OLD FORMAT - working)
test_format_5_old = """
IP: 192.168.1.100
Credentials: admin:password123
Location: Texas (Austin)
ZIP: 78701
"""

# Test Format 5 with NEW Scamalytics fields
test_format_5_new = """
IP: 192.168.1.101
Credentials: user:pass456
Location: US (California, Los Angeles)
ZIP: 90001
Scamalytics Fraud Score: 35
Scamalytics Risk: medium
"""

# Test Format 6 with Scamalytics (with PPTP header)
test_format_6_new = """
> PPTP_SVOIM_VPN:
🚨 PPTP Connection Details
IP: 192.168.1.102
Credentials: vpnuser:vpnpass789
Location: Florida (Miami)
ZIP: 33101
Scamalytics Fraud Score: 75
Scamalytics Risk: high
"""

# Test Format 7 (Simple IP:Login:Pass)
test_format_7 = """
192.168.1.103:testuser:testpass
"""

# Test Format 4 (Colon-separated with country)
test_format_4 = """
192.168.1.104:1723:admin:admin123:United States:New York:10001
"""

# Test mixed formats
test_mixed = """
192.168.1.105:simpleuser:simplepass

IP: 192.168.1.106
Credentials: mixed:password
Location: Texas (Dallas)
ZIP: 75201
Scamalytics Fraud Score: 15
Scamalytics Risk: low

192.168.1.107:1723:user:pass:Canada:Ontario:M5H
"""

print("=" * 80)
print("COMPREHENSIVE PARSING TEST")
print("=" * 80)

# Test 1: Format 5 OLD (without Scamalytics)
print("\n📋 TEST 1: Format 5 (OLD - without Scamalytics)")
print("-" * 80)
result1 = parse_nodes_text(test_format_5_old)
print(f"Parsed nodes: {len(result1['nodes'])}")
if result1['nodes']:
    node = result1['nodes'][0]
    print(f"  IP: {node.get('ip')}")
    print(f"  Login: {node.get('login')}")
    print(f"  State: {node.get('state')}")
    print(f"  City: {node.get('city')}")
    print(f"  ZIP: {node.get('zipcode')}")
    print(f"  Scam Fraud Score: {node.get('scamalytics_fraud_score', 'NOT SET')}")
    print(f"  Scam Risk: {node.get('scamalytics_risk', 'NOT SET')}")
    print(f"  ✅ Format 5 OLD: {'PASSED' if node.get('ip') == '192.168.1.100' else 'FAILED'}")
else:
    print("  ❌ FAILED: No nodes parsed")

# Test 2: Format 5 NEW (with Scamalytics)
print("\n📋 TEST 2: Format 5 (NEW - with Scamalytics)")
print("-" * 80)
result2 = parse_nodes_text(test_format_5_new)
print(f"Parsed nodes: {len(result2['nodes'])}")
if result2['nodes']:
    node = result2['nodes'][0]
    print(f"  IP: {node.get('ip')}")
    print(f"  Login: {node.get('login')}")
    print(f"  Country: {node.get('country')}")
    print(f"  State: {node.get('state')}")
    print(f"  City: {node.get('city')}")
    print(f"  ZIP: {node.get('zipcode')}")
    print(f"  Scam Fraud Score: {node.get('scamalytics_fraud_score')}")
    print(f"  Scam Risk: {node.get('scamalytics_risk')}")
    scam_ok = (node.get('scamalytics_fraud_score') == 35 and 
               node.get('scamalytics_risk') == 'medium')
    print(f"  ✅ Format 5 NEW: {'PASSED' if scam_ok else 'FAILED - Scamalytics not parsed!'}")
else:
    print("  ❌ FAILED: No nodes parsed")

# Test 3: Format 6 with Scamalytics
print("\n📋 TEST 3: Format 6 (with PPTP header + Scamalytics)")
print("-" * 80)
result3 = parse_nodes_text(test_format_6_new)
print(f"Parsed nodes: {len(result3['nodes'])}")
if result3['nodes']:
    node = result3['nodes'][0]
    print(f"  IP: {node.get('ip')}")
    print(f"  Login: {node.get('login')}")
    print(f"  State: {node.get('state')}")
    print(f"  City: {node.get('city')}")
    print(f"  ZIP: {node.get('zipcode')}")
    print(f"  Scam Fraud Score: {node.get('scamalytics_fraud_score')}")
    print(f"  Scam Risk: {node.get('scamalytics_risk')}")
    scam_ok = (node.get('scamalytics_fraud_score') == 75 and 
               node.get('scamalytics_risk') == 'high')
    print(f"  ✅ Format 6 NEW: {'PASSED' if scam_ok else 'FAILED - Scamalytics not parsed!'}")
else:
    print("  ❌ FAILED: No nodes parsed")

# Test 4: Format 7 (Simple)
print("\n📋 TEST 4: Format 7 (Simple IP:Login:Pass)")
print("-" * 80)
result4 = parse_nodes_text(test_format_7)
print(f"Parsed nodes: {len(result4['nodes'])}")
if result4['nodes']:
    node = result4['nodes'][0]
    print(f"  IP: {node.get('ip')}")
    print(f"  Login: {node.get('login')}")
    print(f"  Password: {node.get('password')}")
    print(f"  ✅ Format 7: {'PASSED' if node.get('ip') == '192.168.1.103' else 'FAILED'}")
else:
    print("  ❌ FAILED: No nodes parsed")

# Test 5: Format 4 (Colon-separated)
print("\n📋 TEST 5: Format 4 (Colon-separated)")
print("-" * 80)
result5 = parse_nodes_text(test_format_4)
print(f"Parsed nodes: {len(result5['nodes'])}")
if result5['nodes']:
    node = result5['nodes'][0]
    print(f"  IP: {node.get('ip')}")
    print(f"  Port: {node.get('port')}")
    print(f"  Login: {node.get('login')}")
    print(f"  Country: {node.get('country')}")
    print(f"  State: {node.get('state')}")
    print(f"  ZIP: {node.get('zipcode')}")
    print(f"  ✅ Format 4: {'PASSED' if node.get('ip') == '192.168.1.104' else 'FAILED'}")
else:
    print("  ❌ FAILED: No nodes parsed")

# Test 6: Mixed formats
print("\n📋 TEST 6: Mixed formats (Format 7 + Format 5 + Format 4)")
print("-" * 80)
result6 = parse_nodes_text(test_mixed)
print(f"Parsed nodes: {len(result6['nodes'])}")
print(f"Expected: 3 nodes")
if len(result6['nodes']) == 3:
    print(f"  ✅ Mixed formats: PASSED - All 3 nodes parsed")
    for i, node in enumerate(result6['nodes'], 1):
        print(f"    Node {i}: {node.get('ip')} - {node.get('login')}")
        if node.get('scamalytics_fraud_score'):
            print(f"      Scam: {node.get('scamalytics_fraud_score')} / {node.get('scamalytics_risk')}")
else:
    print(f"  ❌ FAILED: Expected 3 nodes, got {len(result6['nodes'])}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
total_tests = 6
passed_tests = sum([
    len(result1['nodes']) > 0,
    len(result2['nodes']) > 0 and result2['nodes'][0].get('scamalytics_fraud_score') == 35,
    len(result3['nodes']) > 0 and result3['nodes'][0].get('scamalytics_fraud_score') == 75,
    len(result4['nodes']) > 0,
    len(result5['nodes']) > 0,
    len(result6['nodes']) == 3
])

print(f"\n✅ PASSED: {passed_tests}/{total_tests} tests")
print(f"❌ FAILED: {total_tests - passed_tests}/{total_tests} tests")

if passed_tests == total_tests:
    print("\n🎉 ALL PARSING TESTS PASSED!")
    print("✅ Старый формат работает")
    print("✅ Новый формат с Scamalytics работает")
    print("✅ Умный парсинг работает корректно")
else:
    print("\n⚠️ SOME TESTS FAILED - парсинг нуждается в исправлении")
