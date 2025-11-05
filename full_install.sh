#!/bin/bash
################################################################
# Connexa Admin Panel - Full Installation Script
# Полная автоматическая установка приложения с нуля
################################################################

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║        CONNEXA ADMIN PANEL - AUTOMATIC INSTALLATION           ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo bash install.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Running as root${NC}"
echo ""

################################################################
# STEP 1: System packages
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 1/10: Installing system packages..."
echo "════════════════════════════════════════════════════════════════"

if command -v apt-get &> /dev/null; then
    echo "📦 Updating package list..."
    apt-get update -qq
    
    echo "📦 Installing base packages..."
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        ppp \
        pptp-linux \
        sqlite3 \
        curl \
        wget \
        supervisor
    
    echo -e "${GREEN}✅ System packages installed${NC}"
else
    echo -e "${RED}❌ apt-get not found. This script requires Debian/Ubuntu${NC}"
    exit 1
fi
echo ""

################################################################
# STEP 2: Install Node.js and Yarn
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 2/10: Installing Node.js and Yarn..."
echo "════════════════════════════════════════════════════════════════"

if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js 18.x..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
    echo -e "${GREEN}✅ Node.js installed${NC}"
else
    echo "ℹ️  Node.js already installed: $(node --version)"
fi

if ! command -v yarn &> /dev/null; then
    echo "📦 Installing Yarn..."
    npm install -g yarn
    echo -e "${GREEN}✅ Yarn installed${NC}"
else
    echo "ℹ️  Yarn already installed: $(yarn --version)"
fi
echo ""

################################################################
# STEP 3: Create /dev/ppp device
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 3/10: Creating /dev/ppp device..."
echo "════════════════════════════════════════════════════════════════"

if [ -e /dev/ppp ]; then
    echo "ℹ️  /dev/ppp already exists"
else
    echo "🔧 Creating /dev/ppp..."
    mknod /dev/ppp c 108 0
    chmod 600 /dev/ppp
fi

ls -la /dev/ppp
echo -e "${GREEN}✅ /dev/ppp ready${NC}"
echo ""

################################################################
# STEP 4: Setup PPTP config
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 4/10: Setting up PPTP configuration..."
echo "════════════════════════════════════════════════════════════════"

mkdir -p /etc/ppp/peers

cat > /etc/ppp/options.pptp << 'EOF'
lock
noauth
nobsdcomp
nodeflate
EOF

echo -e "${GREEN}✅ PPTP config created${NC}"
echo ""

################################################################
# STEP 5: Install Python dependencies
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 5/10: Installing Python dependencies..."
echo "════════════════════════════════════════════════════════════════"

cd /app/backend

if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Installing Python packages..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo -e "${GREEN}✅ Python dependencies installed${NC}"
echo ""

################################################################
# STEP 6: Install Frontend dependencies
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 6/10: Installing Frontend dependencies..."
echo "════════════════════════════════════════════════════════════════"

cd /app/frontend

if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js packages..."
    yarn install
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo "ℹ️  node_modules already exists, skipping yarn install"
    echo "   Run 'cd /app/frontend && yarn install' manually if needed"
fi
echo ""

################################################################
# STEP 7: Check environment variables
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 7/10: Checking environment variables..."
echo "════════════════════════════════════════════════════════════════"

if [ -f /app/backend/.env ]; then
    echo "✅ Backend .env found"
    if grep -q "ADMIN_SERVER_IP" /app/backend/.env; then
        ADMIN_IP=$(grep ADMIN_SERVER_IP /app/backend/.env | cut -d'=' -f2)
        echo "   ADMIN_SERVER_IP = $ADMIN_IP"
        
        if [ "$ADMIN_IP" == "vpn-tester.preview.emergentagent.com" ]; then
            echo -e "${YELLOW}   ⚠️  Please update ADMIN_SERVER_IP to your actual domain${NC}"
            echo "   Edit: nano /app/backend/.env"
        fi
    else
        echo -e "${YELLOW}   ⚠️  ADMIN_SERVER_IP not found in .env${NC}"
    fi
else
    echo -e "${RED}❌ Backend .env not found${NC}"
fi

if [ -f /app/frontend/.env ]; then
    echo "✅ Frontend .env found"
    if grep -q "REACT_APP_BACKEND_URL" /app/frontend/.env; then
        BACKEND_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d'=' -f2)
        echo "   REACT_APP_BACKEND_URL = $BACKEND_URL"
    fi
else
    echo -e "${YELLOW}⚠️  Frontend .env not found${NC}"
fi
echo ""

################################################################
# STEP 8: Initialize database
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 8/10: Initializing database..."
echo "════════════════════════════════════════════════════════════════"

cd /app/backend
if [ ! -f "connexa.db" ]; then
    echo "🗄️  Creating SQLite database..."
    source venv/bin/activate
    python3 -c "from database import create_tables; create_tables(); print('✅ Database created')"
else
    echo "ℹ️  Database already exists: connexa.db"
fi
echo ""

################################################################
# STEP 9: Setup Supervisor
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 9/10: Setting up Supervisor..."
echo "════════════════════════════════════════════════════════════════"

# Check if supervisor configs already exist
if [ -f /etc/supervisor/conf.d/connexa-backend.conf ]; then
    echo "ℹ️  Supervisor configs already exist"
else
    echo "📝 Creating Supervisor configs..."
    
    # Backend config
    cat > /etc/supervisor/conf.d/connexa-backend.conf << EOF
[program:backend]
command=/app/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
user=root
environment=PATH="/app/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
EOF

    # Frontend config
    cat > /etc/supervisor/conf.d/connexa-frontend.conf << EOF
[program:frontend]
command=/usr/bin/yarn start
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
environment=PATH="/usr/local/bin:/usr/bin:/bin",HOST="0.0.0.0"
user=root
EOF

    echo -e "${GREEN}✅ Supervisor configs created${NC}"
fi

# Reload supervisor
supervisorctl reread
supervisorctl update

echo ""

################################################################
# STEP 10: Start services
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "STEP 10/10: Starting services..."
echo "════════════════════════════════════════════════════════════════"

echo "🔄 Starting backend..."
supervisorctl restart backend

sleep 3

echo "🔄 Starting frontend..."
supervisorctl restart frontend

echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

echo ""
supervisorctl status
echo ""

################################################################
# FINAL CHECKS
################################################################
echo "════════════════════════════════════════════════════════════════"
echo "RUNNING FINAL CHECKS..."
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check backend
echo "🔍 Checking backend API..."
if curl -s http://localhost:8001/api/stats > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API responding${NC}"
else
    echo -e "${YELLOW}⚠️  Backend API not responding yet (may need more time)${NC}"
fi

# Check frontend
echo "🔍 Checking frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend responding${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend not responding yet (may need more time)${NC}"
fi

# Run environment check
echo ""
echo "🔍 Running PPTP environment check..."
if [ -f /app/check_pptp_env.sh ]; then
    bash /app/check_pptp_env.sh
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ INSTALLATION COMPLETE!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🎯 Next steps:"
echo ""
echo "1. Open browser: http://your-domain.com"
echo "2. Login: admin / admin"
echo "3. Select nodes with 'ping_ok' or 'speed_ok' status"
echo "4. Click 'Start Services'"
echo "5. Wait 10-20 seconds for PPTP tunnel"
echo "6. Check SOCKS modal → 'Открыть текстовый файл'"
echo ""
echo "📋 Proxy format:"
echo "   your-domain.com:1083:socks_2:PASSWORD"
echo ""
echo "🧪 Test proxy:"
echo "   curl -x socks5://socks_2:PASSWORD@your-domain.com:1083 https://ifconfig.me"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check for critical issues
ISSUES=0

if ! [ -e /dev/ppp ]; then
    echo -e "${RED}❌ /dev/ppp not found${NC}"
    ISSUES=$((ISSUES + 1))
fi

if ! command -v pppd &> /dev/null; then
    echo -e "${RED}❌ pppd not installed${NC}"
    ISSUES=$((ISSUES + 1))
fi

if ! capsh --print 2>/dev/null | grep -q "cap_net_admin"; then
    echo -e "${YELLOW}⚠️  WARNING: CAP_NET_ADMIN capability missing!${NC}"
    echo "   Docker container needs: --cap-add=NET_ADMIN"
    echo "   PPTP tunnels will NOT work without this!"
    echo ""
fi

if [ $ISSUES -gt 0 ]; then
    echo -e "${RED}Found $ISSUES critical issues. Please fix them before using PPTP.${NC}"
    echo ""
fi

echo "════════════════════════════════════════════════════════════════"
echo "Logs location:"
echo "  Backend: tail -f /var/log/supervisor/backend.err.log"
echo "  Frontend: tail -f /var/log/supervisor/frontend.err.log"
echo "  PPTP: cat /tmp/pptp_node_*.log"
echo "════════════════════════════════════════════════════════════════"
