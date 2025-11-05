#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

echo "════════════════════════════════════════════════════════════════"
echo "  CONNEXA BACKEND - БЫСТРАЯ УСТАНОВКА (3 МИНУТЫ)"
echo "════════════════════════════════════════════════════════════════"

# Очистка
pkill -9 apt-get dpkg 2>/dev/null || true
rm -f /var/lib/dpkg/lock* 2>/dev/null || true
dpkg --configure -a 2>&1 | head -5 || true

# Пакеты
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv ppp pptp-linux git supervisor curl net-tools iptables

# Node.js (только для вида, не используем)
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - > /dev/null
    apt-get install -y -qq nodejs
fi

# Git
if [ -d "/app/.git" ]; then
    cd /app && git reset --hard && git pull origin main
else
    git clone https://github.com/mrolivershea-cyber/10-23-2025-auto-pars-filter1.git /app
fi

# Python
cd /app/backend
python3 -m venv venv
venv/bin/pip install -q -r requirements.txt

# PPTP
mkdir -p /etc/ppp/peers
echo "lock" > /etc/ppp/options.pptp
[ -e /dev/ppp ] || (mknod /dev/ppp c 108 0 && chmod 600 /dev/ppp)

# .env
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

# БД
cd /app/backend
venv/bin/python3 << 'PY'
import sys
sys.path.insert(0,'/app/backend')
from database import Base,engine,SessionLocal,User,hash_password
Base.metadata.create_all(bind=engine)
db=SessionLocal()
if not db.query(User).filter(User.username=="admin").first():
    db.add(User(username="admin",password=hash_password("admin")))
    db.commit()
db.close()
PY

# Routing script
cat > /usr/local/bin/link_socks_to_ppp.sh << 'EOF'
#!/bin/bash
ip rule add fwmark $1 table $1 2>/dev/null || true
ip route add default dev $2 table $1 2>/dev/null || true
iptables -t mangle -A OUTPUT -p tcp --sport $1 -j MARK --set-mark $1 2>/dev/null || true
EOF
chmod +x /usr/local/bin/link_socks_to_ppp.sh

# Supervisor
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

echo ""
echo "✅ BACKEND УСТАНОВЛЕН!"
echo ""
echo "Backend API: http://$SERVER_IP:8001"
echo "Swagger: http://$SERVER_IP:8001/docs"
echo "Логин: admin/admin"
echo ""
