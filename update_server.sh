#!/bin/bash
#
# 🔄 CONNEXA UPGRADE - UPDATE SCRIPT
# Запустите этот скрипт на вашем сервере для обновления до последней версии
#
# Использование:
#   curl -sSL https://raw.githubusercontent.com/mrolivershea-cyber/Connexa-UPGRATE/main/update_server.sh | sudo bash
#

set -e

echo "================================================================================"
echo "🔄 CONNEXA UPGRADE - Обновление до последней версии"
echo "================================================================================"
echo ""

# Определяем директорию установки
if [ -d "/opt/connexa" ]; then
    INSTALL_DIR="/opt/connexa"
elif [ -d "/app" ]; then
    INSTALL_DIR="/app"
else
    echo "❌ Не найдена директория установки Connexa"
    exit 1
fi

echo "📂 Директория: $INSTALL_DIR"

# Backup базы данных
echo ""
echo "📦 Шаг 1/6: Создание backup базы данных..."
if [ -f "$INSTALL_DIR/backend/connexa.db" ]; then
    cp "$INSTALL_DIR/backend/connexa.db" "$INSTALL_DIR/backend/connexa.db.backup_$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup создан"
fi

# Остановка сервисов
echo ""
echo "📦 Шаг 2/6: Остановка сервисов..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl stop connexa-backend connexa-frontend 2>/dev/null || true
    echo "✅ Сервисы остановлены"
fi

# Обновление кода
echo ""
echo "📦 Шаг 3/6: Обновление кода из GitHub..."
cd $INSTALL_DIR
git fetch origin
git reset --hard origin/main
echo "✅ Код обновлен"

# Обновление зависимостей
echo ""
echo "📦 Шаг 4/6: Обновление зависимостей..."

# Backend
cd $INSTALL_DIR/backend
if [ -d "venv" ]; then
    venv/bin/pip install -r requirements.txt --quiet
else
    pip install -r requirements.txt --quiet
fi
echo "✅ Backend зависимости обновлены"

# Frontend
cd $INSTALL_DIR/frontend
yarn install --silent
echo "✅ Frontend зависимости обновлены"

# Пересоздание базы данных
echo ""
echo "📦 Шаг 5/6: Пересоздание базы данных..."
echo "⚠️  ВАЖНО: Старая база сохранена в backup, новая будет пустая"
echo "   Вам нужно будет переимпортировать данные через UI!"

cd $INSTALL_DIR/backend
rm -f connexa.db

# Создание новой базы
if [ -d "venv" ]; then
    venv/bin/python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from database import create_tables
create_tables()
print("✅ Новая база данных создана")
PYEOF
else
    python3 << 'PYEOF'
import sys
sys.path.insert(0, '.')
from database import create_tables
create_tables()
print("✅ Новая база данных создана")
PYEOF
fi

# Запуск сервисов
echo ""
echo "📦 Шаг 6/6: Запуск сервисов..."
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl start connexa-backend connexa-frontend
    sleep 3
    sudo supervisorctl status connexa-backend connexa-frontend
    echo "✅ Сервисы запущены"
fi

echo ""
echo "================================================================================"
echo "🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo "================================================================================"
echo ""
echo "✅ КОД ОБНОВЛЕН до последней версии"
echo "✅ БАЗА ДАННЫХ пересоздана (пустая)"
echo ""
echo "⚠️  СЛЕДУЮЩИЙ ШАГ - ИМПОРТ ДАННЫХ:"
echo ""
echo "1. Откройте админ панель в браузере"
echo "2. Нажмите кнопку 'Import'"
echo "3. Загрузите ваш файл PPTP.txt"
echo "4. Дождитесь завершения импорта"
echo ""
echo "📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:"
echo "  ✅ ВСЕ узлы будут иметь State, City, ZIP"
echo "  ✅ Scamalytics данные (где есть в файле)"
echo "  ✅ Все 15 фильтров работают"
echo ""
echo "================================================================================"
