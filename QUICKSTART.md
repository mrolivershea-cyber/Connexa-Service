# 🚀 БЫСТРЫЙ СТАРТ - 5 ШАГОВ

## Шаг 1: Подготовка сервера (5 мин)
```bash
# Установить пакеты
apt-get update
apt-get install -y ppp pptp-linux

# Создать /dev/ppp
mknod /dev/ppp c 108 0
chmod 600 /dev/ppp
```

## Шаг 2: Запуск с правами (1 мин)
```bash
# Docker с CAP_NET_ADMIN
docker run --cap-add=NET_ADMIN YOUR_IMAGE
# ИЛИ
docker run --privileged YOUR_IMAGE
```

## Шаг 3: Проверка окружения (1 мин)
```bash
bash /app/check_pptp_env.sh
```

**Ожидаем:**
- ✅ /dev/ppp exists
- ✅ pppd found
- ✅ pptp found
- ✅ CAP_NET_ADMIN is present

## Шаг 4: Запуск приложения (2 мин)
```bash
# Backend
cd /app/backend
sudo supervisorctl restart backend

# Frontend
cd /app/frontend
sudo supervisorctl restart frontend
```

## Шаг 5: Тест в UI (2 мин)
1. Логин: admin / admin
2. Выбрать 1-2 узла со статусом ping_ok
3. Нажать "Start Services"
4. Ждать 10-15 секунд
5. Проверить статус → "online" ✅
6. SOCKS → "Открыть текстовый файл" → видим прокси ✅

## ✅ Готово!

Формат прокси:
```
your-domain.com:1083:socks_2:xBivRjFjXVqOVrQS
```

Тест:
```bash
curl -x socks5://socks_2:xBivRjFjXVqOVrQS@your-domain.com:1083 https://ifconfig.me
# Показывает IP PPTP узла
```

## 🆘 Проблемы?

### "Operation not permitted"
→ Docker нужен --cap-add=NET_ADMIN

### "No ppp interface created"
→ Проверить: `cat /tmp/pptp_node_2.log`
→ Credentials правильные?

### "SOCKS connection refused"
→ Проверить: `netstat -tlnp | grep 1083`
→ Firewall?

## 📚 Полная документация
- README_DEPLOYMENT.md - полная инструкция
- PPTP_DEPLOYMENT_GUIDE.md - техническая документация
- check_pptp_env.sh - скрипт проверки
