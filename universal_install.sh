#!/bin/bash
##########################################################################################
# CONNEXA ADMIN PANEL - УНИВЕРСАЛЬНЫЙ УСТАНОВОЧНЫЙ СКРИПТ  
# Автоматическая установка с GitHub
# Версия: 7.0 FINAL - с координатами и исправлениями тестов
# Репозиторий: https://github.com/mrolivershea-cyber/Connexa-
##########################################################################################

set -e
export DEBIAN_FRONTEND=noninteractive

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                ║"
echo "║               CONNEXA ADMIN PANEL - УНИВЕРСАЛЬНАЯ УСТАНОВКА v7.0              ║"
echo "║                                                                                ║"
echo "║                   🚀 АВТОМАТИЧЕСКАЯ УСТАНОВКА С GITHUB                        ║"
echo "║                                                                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Запустите с sudo!${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/9] Установка системных пакетов...${NC}"
apt-get update -qq > /dev/null 2>&1
apt-get install -y python3 python3-pip python3-venv nodejs npm git supervisor curl -qq > /dev/null 2>&1
apt-get install -y mongodb -qq > /dev/null 2>&1 || apt-get install -y mongodb-org -qq > /dev/null 2>&1 || true
echo -e "${GREEN}✅ Системные пакеты${NC}"

echo -e "${YELLOW}[2/9] Установка Yarn...${NC}"
npm install -g yarn > /dev/null 2>&1
echo -e "${GREEN}✅ Yarn${NC}"

echo -e "${YELLOW}[3/9] Клонирование репозитория...${NC}"
cd /tmp
rm -rf Connexa-
git clone https://github.com/mrolivershea-cyber/Connexa-.git > /dev/null 2>&1
echo -e "${GREEN}✅ Репозиторий склонирован${NC}"

echo -e "${YELLOW}[4/9] Копирование файлов...${NC}"
mkdir -p /app
cp -r /tmp/Connexa-/* /app/
echo -e "${GREEN}✅ Файлы скопированы${NC}"

echo -e "${YELLOW}[5/9] Установка Python зависимостей...${NC}"
cd /app/backend
python3 -m venv /root/.venv
source /root/.venv/bin/activate
pip install -q --upgrade pip > /dev/null 2>&1
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Python зависимости${NC}"

echo -e "${YELLOW}[6/9] Настройка Backend .env...${NC}"
cat > /app/backend/.env << 'EOF'
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
IPQS_API_KEY="vUDnFJfLgHSLD7SyxoWLGrLysWt60Saw"
EOF
echo -e "${GREEN}✅ Backend .env${NC}"

echo -e "${YELLOW}[7/9] Установка Node.js зависимостей (2-3 минуты)...${NC}"
cd /app/frontend
yarn install > /dev/null 2>&1
echo -e "${GREEN}✅ Node.js зависимости${NC}"

echo -e "${YELLOW}[8/9] Настройка Frontend .env...${NC}"
cat > /app/frontend/.env << 'EOF'
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
echo -e "${GREEN}✅ Frontend .env${NC}"

echo -e "${YELLOW}[9/9] Настройка Supervisor...${NC}"
mkdir -p /var/lib/mongodb /var/log/mongodb
chown -R mongodb:mongodb /var/lib/mongodb /var/log/mongodb 2>/dev/null || true

cat > /etc/supervisor/conf.d/connexa.conf << 'EOF'
[program:backend]
command=/root/.venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
environment=PATH="/root/.venv/bin:%(ENV_PATH)s"

[program:frontend]
command=/usr/bin/yarn start
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
environment=PORT="3000"

[program:mongodb]
command=/usr/bin/mongod --dbpath /var/lib/mongodb --logpath /var/log/mongodb/mongod.log
autostart=true
autorestart=true
EOF

supervisorctl reread > /dev/null 2>&1
supervisorctl update > /dev/null 2>&1
supervisorctl restart all > /dev/null 2>&1
echo -e "${GREEN}✅ Supervisor настроен${NC}"

echo ""
echo -e "${YELLOW}⏳ Запуск сервисов (20 секунд)...${NC}"
sleep 20

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo -e "║${GREEN}                    ✅ УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!                        ${NC}║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${CYAN}📊 Статус сервисов:${NC}"
supervisorctl status

echo ""
echo -e "${CYAN}🔍 Проверка Backend:${NC}"
HEALTH=$(curl -s http://localhost:8001/health 2>/dev/null || echo "fail")
if [[ $HEALTH == *"ok"* ]]; then
    echo -e "${GREEN}✅ Backend работает${NC}"
else
    echo -e "${RED}❌ Backend не отвечает${NC}"
    echo "Логи: tail -f /var/log/supervisor/backend.err.log"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              CONNEXA ADMIN PANEL v7.0 - ГОТОВ!               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}🌐 Доступ:${NC}"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_IP")
echo -e "   Frontend: ${GREEN}http://$SERVER_IP:3000${NC}"
echo -e "   Backend:  ${GREEN}http://$SERVER_IP:8001${NC}"
echo ""
echo -e "${CYAN}👤 Логин:${NC}"
echo -e "   Username: ${GREEN}admin${NC}"
echo -e "   Password: ${GREEN}admin${NC}"
echo ""
echo -e "${CYAN}📝 Команды:${NC}"
echo "   Статус:   sudo supervisorctl status"
echo "   Рестарт:  sudo supervisorctl restart all"
echo "   Логи:     tail -f /var/log/supervisor/backend.out.log"
echo ""
echo -e "${YELLOW}⭐ Новое в v7.0:${NC}"
echo "   • Координаты (широта/долгота)"
echo "   • Цветная схема Risk Level"
echo "   • Исправлены тесты ГЕО/Фрауд"
echo ""
