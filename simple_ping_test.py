#!/usr/bin/env python3

import sys
import os
sys.path.append('/app/backend')

import asyncio
from ping_speed_test import test_node_ping

async def test_ping_directly():
    """Test ping functionality directly"""
    print("🔥 TESTING PING FUNCTIONALITY DIRECTLY")
    print("=" * 50)
    
    # Test with a known working IP (Google DNS)
    test_ips = [
        "8.8.8.8",  # Google DNS - should be reachable but not PPTP
        "1.1.1.1",  # Cloudflare DNS - should be reachable but not PPTP
        "192.168.1.1"  # Common router IP - might not be reachable
    ]
    
    for ip in test_ips:
        print(f"\n🏓 Testing {ip}...")
        try:
            # Test with fast mode
            result = await test_node_ping(ip, fast_mode=True)
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n✅ Direct ping test completed")

if __name__ == "__main__":
    asyncio.run(test_ping_directly())