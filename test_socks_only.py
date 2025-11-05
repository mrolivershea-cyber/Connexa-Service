#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import ConnexaAPITester

def main():
    """Run only SOCKS Service Launch System tests"""
    tester = ConnexaAPITester()
    
    print("🚀 SOCKS Service Launch System Backend API Testing")
    print("=" * 60)
    
    # Login first
    if not tester.test_login():
        print("❌ Login failed - stopping tests")
        return False
    
    # Run comprehensive SOCKS tests
    tester.run_comprehensive_socks_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 SOCKS Test Summary: {tester.tests_passed}/{tester.tests_run} tests passed")
    print(f"✅ Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    return tester.tests_passed == tester.tests_run

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)