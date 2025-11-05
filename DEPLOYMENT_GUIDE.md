# 🚀 DEPLOYMENT GUIDE - РЕАЛЬНЫЙ VPN SPEED TEST

## 📋 ЧТО НУЖНО НА ВАШЕМ СЕРВЕРЕ

### Требования:
- Ubuntu 20.04+ / Debian 11+
- Root доступ
- Docker (опционально)
- Минимум 2GB RAM
- Python 3.9+

---

## 🔧 ВАРИАНТ 1: ПРЯМАЯ УСТАНОВКА НА СЕРВЕР

### Шаг 1: Установка зависимостей

```bash
# Обновляем систему
apt-get update && apt-get upgrade -y

# Устанавливаем PPTP клиент и ppp
apt-get install -y pptp-linux ppp

# Устанавливаем Python и зависимости
apt-get install -y python3 python3-pip python3-venv

# Устанавливаем Node.js (для frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Устанавливаем MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
apt-get update
apt-get install -y mongodb-org
systemctl start mongod
systemctl enable mongod
```

### Шаг 2: Клонирование проекта

```bash
# Создаем директорию
mkdir -p /opt/netprobe
cd /opt/netprobe

# Копируем все файлы из текущего проекта
# (вы можете использовать git clone или scp)
```

### Шаг 3: Настройка PPTP с правами root

```bash
# Создаем конфигурацию PPP с правильными правами
cat > /etc/ppp/options.pptp << 'EOF'
noauth
refuse-eap
refuse-pap
refuse-chap
refuse-mschap
require-mppe-128
nobsdcomp
nodeflate
novj
novjccomp
lcp-echo-interval 0
lcp-echo-failure 0
EOF

# Даем права
chmod 644 /etc/ppp/options.pptp
chmod 755 /etc/ppp/peers
```

### Шаг 4: Установка Python зависимостей

```bash
cd /opt/netprobe/backend

# Создаем virtual environment
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### Шаг 5: Настройка переменных окружения

```bash
# Backend .env
cat > /opt/netprobe/backend/.env << 'EOF'
MONGO_URL=mongodb://localhost:27017/netprobe
SECRET_KEY=your_secret_key_here
EOF

# Frontend .env
cat > /opt/netprobe/frontend/.env << 'EOF'
REACT_APP_BACKEND_URL=http://your-server-ip:8001
EOF
```

### Шаг 6: Запуск сервисов

```bash
# Backend
cd /opt/netprobe/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 &

# Frontend
cd /opt/netprobe/frontend
npm install
npm start &
```

---

## 🐳 ВАРИАНТ 2: DOCKER С ПРИВИЛЕГИЯМИ (РЕКОМЕНДУЕТСЯ)

### Dockerfile для backend с PPTP

```dockerfile
FROM python:3.11-slim

# Устанавливаем PPTP клиент
RUN apt-get update && apt-get install -y \
    pptp-linux \
    ppp \
    iptables \
    iproute2 \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY backend/ .

# Настраиваем PPTP
RUN mkdir -p /etc/ppp/peers && \
    echo "noauth\nrefuse-eap\nrefuse-pap\nrefuse-chap\nrefuse-mschap\nrequire-mppe-128" > /etc/ppp/options.pptp

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### docker-compose.yml с привилегиями

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    restart: always
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    restart: always
    privileged: true  # КРИТИЧЕСКИ ВАЖНО для PPTP!
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    devices:
      - /dev/ppp:/dev/ppp
    volumes:
      - ./backend:/app
      - /etc/ppp:/etc/ppp:rw
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongodb:27017/netprobe
    depends_on:
      - mongodb

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    restart: always
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://your-server-ip:8001
    depends_on:
      - backend

volumes:
  mongodb_data:
```

### Запуск через Docker

```bash
# Клонируем проект
cd /opt/netprobe

# Запускаем с привилегиями
docker-compose up -d

# Проверяем логи
docker-compose logs -f backend
```

---

## 🧪 ТЕСТИРОВАНИЕ VPN ТУННЕЛЯ

### Тест вручную (после установки):

```bash
# Создаем тестовую конфигурацию PPTP
cat > /etc/ppp/peers/testnode << 'EOF'
pty "pptp 24.227.222.163 --nolaunchpppd"
name admin
password admin
remotename PPTP
require-mppe-128
refuse-eap
refuse-pap
refuse-chap
refuse-mschap
file /etc/ppp/options.pptp
ipparam PPTP
noauth
EOF

# Запускаем туннель
pon testnode updetach

# Проверяем что туннель поднялся
ip link show | grep ppp

# Проверяем IP через туннель
ip addr show ppp0

# Тестируем ping
ping -I ppp0 -c 5 8.8.8.8

# Закрываем туннель
poff testnode
```

---

## 📝 ИНСТРУКЦИИ ДЛЯ ВАС

### Что нужно сделать:

1. **Выберите сервер**: Ubuntu 20.04+ или Debian 11+
2. **Дайте мне:**
   - IP адрес сервера
   - SSH доступ (или вы сами выполните команды)
   
3. **Я подготовлю:**
   - Полный deployment package
   - Все скрипты установки
   - Конфигурации
   
4. **Вы развернете:**
   - По моим инструкциям
   - Или я помогу через пошаговые команды

### Формат передачи кода:

**Опция A**: Вы копируете текущий проект
```bash
# На Emergent
tar -czf netprobe.tar.gz /app

# Копируете на ваш сервер
scp netprobe.tar.gz your-server:/opt/
```

**Опция B**: Я создаю deployment package здесь
```bash
# Создам zip с всем необходимым
# Вы скачаете и развернете
```

---

## ⚡ БЫСТРЫЙ СТАРТ (1 команда)

После того как вы дадите мне знать о сервере, я создам:

```bash
# Один скрипт который все сделает
curl -sSL https://your-link/install.sh | bash
```

---

## 🎯 ГОТОВ ПОМОЧЬ

Скажите:
1. ✅ Какой вариант предпочитаете? (Прямая установка / Docker)
2. ✅ У вас есть сервер готовый?
3. ✅ Хотите полный deployment package?

Я подготовлю ВСЕ необходимое! 🚀
