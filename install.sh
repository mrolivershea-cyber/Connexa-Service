#!/bin/bash
################################################################
# PPTP + SOCKS5 Automatic Installation Script
# Автоматическая установка всех компонентов
################################################################

set -e  # Exit on error

echo "================================================================"
echo "  PPTP + SOCKS5 INSTALLATION SCRIPT"
echo "================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root (sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Running as root${NC}"
echo ""

################################################################
# STEP 1: Install system packages
################################################################
echo "================================================================"
echo "STEP 1: Installing system packages..."
echo "================================================================"

if command -v apt-get &> /dev/null; then
    echo "📦 Updating package list..."
    apt-get update -qq
    
    echo "📦 Installing ppp and pptp-linux..."
    apt-get install -y ppp pptp-linux
    
    echo -e "${GREEN}✅ Packages installed${NC}"
else
    echo -e "${RED}❌ apt-get not found. This script requires Debian/Ubuntu${NC}"
    exit 1
fi
echo ""

################################################################
# STEP 2: Create /dev/ppp device
################################################################
echo "================================================================"
echo "STEP 2: Creating /dev/ppp device..."
echo "================================================================"

if [ -e /dev/ppp ]; then
    echo "ℹ️  /dev/ppp already exists"
    ls -la /dev/ppp
else
    echo "🔧 Creating /dev/ppp..."
    mknod /dev/ppp c 108 0
    chmod 600 /dev/ppp
    
    if [ -e /dev/ppp ]; then
        echo -e "${GREEN}✅ /dev/ppp created successfully${NC}"
        ls -la /dev/ppp
    else
        echo -e "${RED}❌ Failed to create /dev/ppp${NC}"
        exit 1
    fi
fi
echo ""

################################################################
# STEP 3: Create /etc/ppp/options.pptp
################################################################
echo "================================================================"
echo "STEP 3: Creating /etc/ppp/options.pptp..."
echo "================================================================"

cat > /etc/ppp/options.pptp << 'EOF'
lock
noauth
nobsdcomp
nodeflate
EOF

echo -e "${GREEN}✅ /etc/ppp/options.pptp created${NC}"
echo ""

################################################################
# STEP 4: Check environment
################################################################
echo "================================================================"
echo "STEP 4: Checking environment..."
echo "================================================================"

# Check pppd
if command -v pppd &> /dev/null; then
    echo -e "${GREEN}✅ pppd found: $(which pppd)${NC}"
else
    echo -e "${RED}❌ pppd not found${NC}"
    exit 1
fi

# Check pptp
if command -v pptp &> /dev/null; then
    echo -e "${GREEN}✅ pptp found: $(which pptp)${NC}"
else
    echo -e "${RED}❌ pptp not found${NC}"
    exit 1
fi

# Check /dev/ppp
if [ -e /dev/ppp ]; then
    echo -e "${GREEN}✅ /dev/ppp exists${NC}"
else
    echo -e "${RED}❌ /dev/ppp not found${NC}"
    exit 1
fi

# Check capabilities
if command -v capsh &> /dev/null; then
    if capsh --print 2>/dev/null | grep -q "cap_net_admin"; then
        echo -e "${GREEN}✅ CAP_NET_ADMIN capability present${NC}"
    else
        echo -e "${YELLOW}⚠️  CAP_NET_ADMIN capability missing${NC}"
        echo "   Container needs --cap-add=NET_ADMIN or --privileged"
    fi
else
    echo -e "${YELLOW}⚠️  Cannot check capabilities (capsh not installed)${NC}"
fi
echo ""

################################################################
# STEP 5: Restart services
################################################################
echo "================================================================"
echo "STEP 5: Restarting services..."
echo "================================================================"

if command -v supervisorctl &> /dev/null; then
    echo "🔄 Restarting backend..."
    supervisorctl restart backend
    
    echo "🔄 Restarting frontend..."
    supervisorctl restart frontend
    
    echo -e "${GREEN}✅ Services restarted${NC}"
else
    echo -e "${YELLOW}⚠️  supervisorctl not found, skipping service restart${NC}"
    echo "   Please restart services manually"
fi
echo ""

################################################################
# STEP 6: Run environment check
################################################################
echo "================================================================"
echo "STEP 6: Running environment check..."
echo "================================================================"

if [ -f /app/check_pptp_env.sh ]; then
    bash /app/check_pptp_env.sh
else
    echo -e "${YELLOW}⚠️  check_pptp_env.sh not found${NC}"
    echo "   Make sure all files are copied to /app/"
fi
echo ""

################################################################
# SUMMARY
################################################################
echo "================================================================"
echo "INSTALLATION COMPLETE!"
echo "================================================================"
echo ""
echo "Next steps:"
echo "1. Open admin panel: https://your-domain.com"
echo "2. Login: admin / admin"
echo "3. Select nodes with 'ping_ok' or 'speed_ok' status"
echo "4. Click 'Start Services'"
echo "5. Wait 10-20 seconds"
echo "6. Check SOCKS modal -> 'Открыть текстовый файл'"
echo ""
echo "Test proxy:"
echo "  curl -x socks5://socks_2:PASSWORD@your-domain.com:1083 https://ifconfig.me"
echo ""
echo -e "${GREEN}✅ Installation successful!${NC}"
echo ""

################################################################
# Check for issues
################################################################
if [ ! -f /app/backend/pptp_tunnel_manager.py ]; then
    echo -e "${RED}⚠️  WARNING: pptp_tunnel_manager.py not found in /app/backend/${NC}"
    echo "   Please copy all files from archive first"
    echo ""
fi

if ! capsh --print 2>/dev/null | grep -q "cap_net_admin"; then
    echo -e "${YELLOW}⚠️  WARNING: CAP_NET_ADMIN capability missing${NC}"
    echo "   PPTP tunnels will NOT work without this capability"
    echo "   Please restart container with: --cap-add=NET_ADMIN"
    echo ""
fi

echo "================================================================"
echo "For troubleshooting, check:"
echo "  - Backend logs: tail -100 /var/log/supervisor/backend.err.log"
echo "  - PPTP logs: cat /tmp/pptp_node_*.log"
echo "  - Environment: bash /app/check_pptp_env.sh"
echo "================================================================"
