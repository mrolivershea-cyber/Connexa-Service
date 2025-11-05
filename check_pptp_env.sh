#!/bin/bash
# PPTP Environment Check Script

echo "=================================="
echo "PPTP Environment Check"
echo "=================================="
echo ""

# Check 1: /dev/ppp
echo "1. Checking /dev/ppp device..."
if [ -e /dev/ppp ]; then
    ls -la /dev/ppp
    echo "✅ /dev/ppp exists"
else
    echo "❌ /dev/ppp does not exist"
    echo "   Creating /dev/ppp..."
    mknod /dev/ppp c 108 0 2>/dev/null && chmod 600 /dev/ppp
    if [ -e /dev/ppp ]; then
        echo "✅ /dev/ppp created successfully"
    else
        echo "❌ Failed to create /dev/ppp"
    fi
fi
echo ""

# Check 2: pppd
echo "2. Checking pppd..."
if command -v pppd &> /dev/null; then
    echo "✅ pppd found: $(which pppd)"
    pppd --version 2>&1 | head -1
else
    echo "❌ pppd not found - install with: apt-get install ppp"
fi
echo ""

# Check 3: pptp
echo "3. Checking pptp..."
if command -v pptp &> /dev/null; then
    echo "✅ pptp found: $(which pptp)"
else
    echo "❌ pptp not found - install with: apt-get install pptp-linux"
fi
echo ""

# Check 4: Capabilities
echo "4. Checking capabilities..."
if command -v capsh &> /dev/null; then
    echo "Current capabilities:"
    capsh --print | grep Current
    if capsh --print | grep -q "cap_net_admin"; then
        echo "✅ CAP_NET_ADMIN is present"
    else
        echo "❌ CAP_NET_ADMIN is missing"
        echo "   Need to run container with --cap-add=NET_ADMIN"
    fi
else
    echo "⚠️ capsh not available, skipping capability check"
fi
echo ""

# Check 5: Test /dev/ppp access
echo "5. Testing /dev/ppp access..."
if timeout 1 cat /dev/ppp 2>&1 | grep -q "Operation not permitted"; then
    echo "❌ /dev/ppp access denied - need CAP_NET_ADMIN"
elif [ -r /dev/ppp ]; then
    echo "✅ /dev/ppp is readable"
else
    echo "⚠️ Cannot determine /dev/ppp access"
fi
echo ""

# Check 6: ppp interfaces
echo "6. Checking existing ppp interfaces..."
if command -v ifconfig &> /dev/null; then
    ppp_count=$(ifconfig | grep -c "^ppp")
    if [ $ppp_count -gt 0 ]; then
        echo "✅ Found $ppp_count ppp interface(s):"
        ifconfig | grep "^ppp" -A 3
    else
        echo "ℹ️  No ppp interfaces found (normal if no tunnels active)"
    fi
else
    echo "⚠️ ifconfig not available"
fi
echo ""

# Check 7: SOCKS servers
echo "7. Checking SOCKS servers..."
if command -v netstat &> /dev/null; then
    socks_count=$(netstat -tlnp 2>/dev/null | grep -E "108[0-9]" | wc -l)
    if [ $socks_count -gt 0 ]; then
        echo "✅ Found $socks_count SOCKS server(s):"
        netstat -tlnp 2>/dev/null | grep -E "108[0-9]"
    else
        echo "ℹ️  No SOCKS servers found (normal if no services started)"
    fi
else
    echo "⚠️ netstat not available"
fi
echo ""

# Summary
echo "=================================="
echo "Summary"
echo "=================================="
if [ -e /dev/ppp ] && command -v pppd &> /dev/null && command -v pptp &> /dev/null; then
    echo "✅ Basic PPTP requirements met"
    echo ""
    echo "Next steps:"
    echo "1. Make sure container has CAP_NET_ADMIN"
    echo "2. Test PPTP tunnel manually (see PPTP_DEPLOYMENT_GUIDE.md)"
    echo "3. Start SOCKS service from admin panel"
else
    echo "❌ Some requirements missing"
    echo ""
    echo "Install missing packages:"
    echo "  apt-get update && apt-get install -y ppp pptp-linux"
fi
echo ""
