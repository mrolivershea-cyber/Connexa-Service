#!/bin/bash
#
# 🚀 CONNEXA UPGRADED VERSION - ONE COMMAND INSTALL
# Репозиторий: https://github.com/mrolivershea-cyber/Connexa-UPGRATE
#
# Что включено:
# ✅ Исправленные фильтры (все 15 фильтров работают)
# ✅ Супер-гибкий парсер Location (14 вариаций формата)
# ✅ Поддержка Scamalytics (Fraud Score + Risk Level)
# ✅ Speed фильтры (speed_min, speed_max)
# ✅ Исправлены импорты и race conditions
# ✅ Улучшенная функция копирования (работает везде)
# ✅ Chunked import для больших файлов
#

set -e  # Exit on any error

echo "================================================================================"
echo "🚀 CONNEXA UPGRADED - АВТОМАТИЧЕСКАЯ УСТАНОВКА"
echo "================================================================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Шаг 1/7: Клонирование репозитория...${NC}"
if [ -d "/app" ]; then
    echo "⚠️  Директория /app уже существует. Удаляем старую версию..."
    cd /tmp
    rm -rf /app
fi

git clone https://github.com/mrolivershea-cyber/Connexa-UPGRATE.git /app
cd /app

echo -e "${GREEN}✅ Репозиторий клонирован${NC}"

echo -e "${BLUE}📦 Шаг 2/7: Установка backend зависимостей...${NC}"
cd /app/backend

# Установка Python зависимостей
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✅ Python зависимости установлены${NC}"
else
    echo -e "${RED}❌ Файл requirements.txt не найден${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Шаг 3/7: Установка frontend зависимостей...${NC}"
cd /app/frontend

# Установка Node.js зависимостей
if [ -f "package.json" ]; then
    yarn install --silent
    echo -e "${GREEN}✅ Frontend зависимости установлены${NC}"
else
    echo -e "${RED}❌ Файл package.json не найден${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Шаг 4/7: Создание .env файлов...${NC}"

# Backend .env
if [ ! -f "/app/backend/.env" ]; then
    cat > /app/backend/.env << 'ENVEOF'
SECRET_KEY=connexa-secret-key-change-in-production
DATABASE_URL=sqlite:///./connexa.db
CORS_ORIGINS=*
ENVEOF
    echo -e "${GREEN}✅ Backend .env создан${NC}"
fi

# Frontend .env
if [ ! -f "/app/frontend/.env" ]; then
    # Попробуем определить BACKEND_URL автоматически
    if [ -n "$REACT_APP_BACKEND_URL" ]; then
        BACKEND_URL="$REACT_APP_BACKEND_URL"
    else
        BACKEND_URL="http://localhost:8001/api"
    fi
    
    cat > /app/frontend/.env << ENVEOF
REACT_APP_BACKEND_URL=$BACKEND_URL
ENVEOF
    echo -e "${GREEN}✅ Frontend .env создан с URL: $BACKEND_URL${NC}"
    echo -e "${BLUE}   ⚠️  ВАЖНО: Измените REACT_APP_BACKEND_URL на ваш production URL!${NC}"
fi

echo -e "${BLUE}📦 Шаг 5/7: Инициализация базы данных...${NC}"
cd /app/backend

# Создание таблиц через Python
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/app/backend')
from database import create_tables
create_tables()
print("✅ Таблицы базы данных созданы")
PYEOF

echo -e "${GREEN}✅ База данных инициализирована${NC}"

echo -e "${BLUE}📦 Шаг 6/7: Сборка frontend...${NC}"
cd /app/frontend
yarn build --silent

echo -e "${GREEN}✅ Frontend собран${NC}"

echo -e "${BLUE}📦 Шаг 7/7: Запуск сервисов...${NC}"

# Проверяем наличие supervisor
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart all
    echo -e "${GREEN}✅ Сервисы перезапущены через supervisor${NC}"
else
    echo -e "${BLUE}ℹ️  Supervisor не найден. Запускайте вручную:${NC}"
    echo ""
    echo "  Backend:  cd /app/backend && uvicorn server:app --host 0.0.0.0 --port 8001"
    echo "  Frontend: cd /app/frontend && yarn start"
    echo ""
fi

echo ""
echo "================================================================================"
echo -e "${GREEN}🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!${NC}"
echo "================================================================================"
echo ""
echo "📊 ЧТО УСТАНОВЛЕНО:"
echo "  ✅ Backend: FastAPI + SQLite (порт 8001)"
echo "  ✅ Frontend: React (порт 3000)"
echo "  ✅ Все 15 фильтров работают"
echo "  ✅ Супер-гибкий парсер (14 форматов Location)"
echo "  ✅ Scamalytics поддержка (Fraud Score + Risk)"
echo "  ✅ Chunked import для больших файлов"
echo ""
echo "🔐 ДОСТУП:"
echo "  Username: admin"
echo "  Password: admin"
echo ""
echo "🌐 URLS:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001/api"
echo "  Backend Docs: http://localhost:8001/docs"
echo ""
echo "📚 ДОКУМЕНТАЦИЯ:"
echo "  README: /app/README.md"
echo "  API Docs: http://localhost:8001/docs"
echo ""
echo "================================================================================"
