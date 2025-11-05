#!/bin/bash
#
# CONNEXA UPGRADED - DIRECT INSTALL (без GitHub)
# Устанавливает текущую версию напрямую
#

set -e

echo "🚀 CONNEXA UPGRADED - Прямая установка"
echo "======================================"

# Проверка что мы в правильной директории
if [ ! -d "/app/backend" ] || [ ! -d "/app/frontend" ]; then
    echo "❌ Ошибка: Запустите этот скрипт изнутри проекта Emergent"
    exit 1
fi

cd /app

echo ""
echo "📦 Шаг 1/6: Установка backend зависимостей..."
cd /app/backend
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo "✅ Backend зависимости установлены"
fi

echo ""
echo "📦 Шаг 2/6: Установка frontend зависимостей..."
cd /app/frontend
if [ -f "package.json" ]; then
    yarn install --silent
    echo "✅ Frontend зависимости установлены"
fi

echo ""
echo "📦 Шаг 3/6: Проверка .env файлов..."

# Backend .env
if [ ! -f "/app/backend/.env" ]; then
    cat > /app/backend/.env << 'EOF'
SECRET_KEY=connexa-secret
DATABASE_URL=sqlite:///./connexa.db
CORS_ORIGINS=*
EOF
    echo "✅ Backend .env создан"
fi

# Frontend .env  
if [ ! -f "/app/frontend/.env" ]; then
    BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8001/api}"
    cat > /app/frontend/.env << EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
EOF
    echo "✅ Frontend .env создан"
fi

echo ""
echo "📦 Шаг 4/6: Инициализация базы данных..."
cd /app/backend
python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from database import create_tables
create_tables()
print("✅ База данных инициализирована")
PYEOF

echo ""
echo "📦 Шаг 5/6: Перезапуск backend..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart backend
    echo "✅ Backend перезапущен"
else
    echo "⚠️  Supervisor не найден, пропускаем"
fi

echo ""
echo "📦 Шаг 6/6: Перезапуск frontend..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart frontend
    echo "✅ Frontend перезапущен"
else
    echo "⚠️  Supervisor не найден, пропускаем"
fi

echo ""
echo "======================================"
echo "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo "======================================"
echo ""
echo "✅ ВСЕ УЛУЧШЕНИЯ ПРИМЕНЕНЫ:"
echo "  - Исправлены фильтры (15 фильтров работают)"
echo "  - Супер-парсер Location (14 форматов)"
echo "  - Scamalytics поддержка"
echo "  - Speed фильтры"
echo "  - Устранен Race Condition"
echo ""
echo "🌐 Доступ: http://localhost:3000"
echo "🔐 Login: admin / Password: admin"
echo ""
