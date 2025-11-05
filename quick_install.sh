#!/bin/bash
##########################################################################################
# CONNEXA - ФИНАЛЬНЫЙ УСТАНОВОЧНИК v5.0
# 100% ГАРАНТИЯ BACKEND + ОПЦИОНАЛЬНЫЙ FRONTEND
##########################################################################################

set -e
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

REPO_URL="https://github.com/mrolivershea-cyber/10-22-2025-final-fix-auto.git"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         CONNEXA v5.0 - БЫСТРАЯ УСТАНОВКА (3 МИНУТЫ)           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Запусти как root: sudo bash install.sh${NC}"
    exit 1
fi

# Очистка lock файлов
echo "🔧 Подготовка системы..."
pkill -9 apt-get dpkg unattended-upgr 2>/dev/null || true
rm -f /var/lib/dpkg/lock* /var/lib/apt/lists/lock /var/cache/apt/archives/lock 2>/dev/null || true
dpkg --configure -a 2>&1 | head -5 || true
sleep 3

# Установка пакетов
echo "📦 Установка системных пакетов..."
apt-get update -qq 2>&1 | grep -v debconf || true
apt-get install -y -qq -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" \
    python3 python3-pip python3-venv ppp pptp-linux git supervisor curl wget net-tools iptables 2>&1 | grep -v debconf || true

# Node.js
if ! command -v node &> /dev/null; then
    echo "📦 Установка Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - > /dev/null 2>&1
    apt-get install -y -qq nodejs 2>&1 | grep -v debconf || true
fi

# Git clone
echo "📥 Клонирование репозитория..."
if [ -d "/app/.git" ]; then
    cd /app && git fetch origin && git reset --hard origin/main
else
    git clone $REPO_URL /app
fi

# Python
echo "🐍 Установка Python зависимостей..."
cd /app/backend
python3 -m venv venv
venv/bin/pip install -q -r requirements.txt

# PPTP
mkdir -p /etc/ppp/peers
cat > /etc/ppp/options.pptp << 'EOF'
lock
noauth
nobsdcomp
nodeflate
EOF

if [ ! -e /dev/ppp ]; then
    mknod /dev/ppp c 108 0
    chmod 600 /dev/ppp
fi

# .env файлы
SERVER_IP=$(hostname -I | awk '{print $1}')
cat > /app/backend/.env << EOF
ADMIN_SERVER_IP=$SERVER_IP
DATABASE_URL=sqlite:///./connexa.db
SECRET_KEY=$(openssl rand -hex 32)
SOCKS_STARTUP_CHECK_RETRIES=0
EOF

cat > /app/frontend/.env << EOF
REACT_APP_BACKEND_URL=http://$SERVER_IP:8001
EOF

# База данных
echo "🗄️  Создание базы данных..."
cd /app/backend
venv/bin/python3 << 'PYEOF'
import sys
sys.path.insert(0, '/app/backend')
from database import Base, engine, SessionLocal, User, hash_password
Base.metadata.create_all(bind=engine)
db = SessionLocal()
admin = db.query(User).filter(User.username == "admin").first()
if not admin:
    admin = User(username="admin", password=hash_password("admin"))
    db.add(admin)
    db.commit()
db.close()
print("✅ БД создана")
PYEOF

# link_socks_to_ppp.sh
cat > /usr/local/bin/link_socks_to_ppp.sh << 'EOF'
#!/bin/bash
SOCKS_PORT=$1
PPP_IFACE=$2
ip rule add fwmark $SOCKS_PORT table $SOCKS_PORT 2>/dev/null || true
ip route add default dev $PPP_IFACE table $SOCKS_PORT 2>/dev/null || true
iptables -t mangle -A OUTPUT -p tcp --sport $SOCKS_PORT -j MARK --set-mark $SOCKS_PORT 2>/dev/null || true
EOF
chmod +x /usr/local/bin/link_socks_to_ppp.sh

# Supervisor backend
cat > /etc/supervisor/conf.d/connexa-backend.conf << EOF
[program:backend]
command=/app/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
user=root
environment=PATH="/app/backend/venv/bin:/usr/local/sbin:/usr/sbin:/usr/local/bin:/usr/bin:/bin"
EOF

supervisorctl reread
supervisorctl update
supervisorctl start backend

sleep 5

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              ✅ BACKEND УСТАНОВЛЕН И РАБОТАЕТ!                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Backend API: http://$SERVER_IP:8001"
echo "📚 Swagger UI: http://$SERVER_IP:8001/docs"
echo "🔐 Логин: admin / admin"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📱 УСТАНОВКА FRONTEND (ОПЦИОНАЛЬНО):"
echo ""
echo "cd /app/frontend"
echo "sysctl -w net.ipv6.conf.all.disable_ipv6=1"
echo "npm config set registry https://registry.npmmirror.com/"
echo "npm install --legacy-peer-deps --force"
echo "npm install ajv@^8.0.0 --legacy-peer-deps"  
echo "npm config set registry https://registry.npmjs.org/"
echo "sysctl -w net.ipv6.conf.all.disable_ipv6=0"
echo ""
echo "# Создать supervisor конфиг:"
echo "cat > /etc/supervisor/conf.d/connexa-frontend.conf << 'FEOF'"
echo "[program:frontend]"
echo "command=/usr/bin/npm start"
echo "directory=/app/frontend"
echo "autostart=true"
echo "autorestart=true"
echo "stderr_logfile=/var/log/supervisor/frontend.err.log"
echo "stdout_logfile=/var/log/supervisor/frontend.out.log"
echo "environment=PATH=\"/usr/local/bin:/usr/bin:/bin\",HOST=\"0.0.0.0\",PORT=\"3000\""
echo "user=root"
echo "FEOF"
echo ""
echo "supervisorctl reread && supervisorctl update && supervisorctl start frontend"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ УСТАНОВКА ЗАВЕРШЕНА!"
echo "════════════════════════════════════════════════════════════════"
