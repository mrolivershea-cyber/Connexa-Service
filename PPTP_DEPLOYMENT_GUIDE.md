# PPTP + SOCKS5 Deployment Guide

## Системные требования

### 1. Docker контейнер должен быть запущен с правами:
```bash
docker run --cap-add=NET_ADMIN ...
# ИЛИ
docker run --privileged ...
```

### 2. Необходимые пакеты (уже установлены):
- ppp (2.4.9+)
- pptp-linux (1.10.0+)

### 3. Проверка /dev/ppp:
```bash
ls -la /dev/ppp
# Должен быть: crw------- 1 root root 108, 0
```

Если не существует:
```bash
mknod /dev/ppp c 108 0
chmod 600 /dev/ppp
```

### 4. Проверка модулей ядра (опционально):
```bash
modprobe ppp_generic
modprobe ppp_async  
modprobe ppp_mppe
```

## Архитектура

```
Клиент 
  ↓
SOCKS5 Proxy (порт 1083, 1084, etc.) на админ сервере
  ↓
PPTP туннель (ppp0, ppp1, etc.)
  ↓
VPN узел (PPTP сервер)
  ↓
Интернет
```

## Как это работает

### Start Service (Запуск):
1. Проверяется PPTP соединение к узлу
2. Создается peer config в `/etc/ppp/peers/pptp_node_{id}`
3. Запускается `pppd call pptp_node_{id}`
4. Ожидается создание ppp интерфейса (ppp0, ppp1, etc.)
5. Запускается SOCKS5 сервер на уникальном порту
6. SOCKS5 привязывается к IP адресу ppp интерфейса
7. Весь трафик через SOCKS5 идет через PPTP туннель
8. Статус узла меняется на "online"
9. Данные сохраняются в БД

### Stop Service (Остановка):
1. Останавливается SOCKS5 сервер
2. Завершается процесс pppd (kill PID)
3. Удаляется ppp интерфейс
4. Удаляется peer config
5. Очищаются данные из БД
6. Статус узла возвращается в "ping_ok"

## Тестирование

### 1. Проверка прав:
```bash
# Внутри контейнера
cat /proc/1/status | grep Cap
# Должен содержать CAP_NET_ADMIN (12 бит)
```

### 2. Ручной тест PPTP:
```bash
# Создать тестовый peer
cat > /etc/ppp/peers/test << EOF
pty "pptp 144.229.29.35 --nolaunchpppd"
name admin
password admin
remotename PPTP
require-mppe-128
file /etc/ppp/options.pptp
nodefaultroute
noauth
EOF

# Запустить
pppd call test nodetach
# Должен создаться ppp0 интерфейс
```

### 3. Проверка интерфейсов:
```bash
ifconfig | grep ppp
# Должны быть: ppp0, ppp1, etc.
```

### 4. Проверка SOCKS серверов:
```bash
netstat -tlnp | grep python
# Должны быть порты 1083, 1084, etc.
```

### 5. Тест подключения через curl:
```bash
# Через SOCKS5
curl -x socks5://socks_2:PASSWORD@vpn-tester.preview.emergentagent.com:1083 https://ifconfig.me
# Должен показать IP PPTP узла
```

## Формат прокси файла

```
vpn-tester.preview.emergentagent.com:1083:socks_2:xBivRjFjXVqOVrQS
vpn-tester.preview.emergentagent.com:1084:socks_3:JW3XvSUHKKBY1s0T
```

Формат: `DOMAIN:PORT:LOGIN:PASSWORD`

## Troubleshooting

### Ошибка: "Operation not permitted"
**Причина:** Нет CAP_NET_ADMIN capability
**Решение:** Запустить контейнер с `--cap-add=NET_ADMIN`

### Ошибка: "No such device"
**Причина:** /dev/ppp не существует
**Решение:** 
```bash
mknod /dev/ppp c 108 0
chmod 600 /dev/ppp
```

### Ошибка: "Timeout waiting for ppp interface"
**Причина:** PPTP соединение не установлено
**Решение:** 
- Проверить credentials узла (login/password)
- Проверить доступность узла (ping)
- Проверить логи: `cat /tmp/pptp_node_X.log`

### PPTP туннель создается но трафик не идет
**Причина:** Routing не настроен
**Решение:** SOCKS5 привязывается к IP ppp интерфейса автоматически

## Логи

- Backend: `/var/log/supervisor/backend.err.log`
- PPTP логи: `/tmp/pptp_node_{id}.log`
- Peer configs: `/etc/ppp/peers/pptp_node_{id}`

## Безопасность

- PPTP credentials берутся из БД (node.login, node.password)
- SOCKS credentials автогенерируются (16 символов)
- Каждый узел имеет уникальный порт (1081-9999)
- Логин формат: `socks_{node_id}`

## Production checklist

- [ ] Docker контейнер запущен с `--cap-add=NET_ADMIN`
- [ ] /dev/ppp существует и доступен
- [ ] ppp и pptp-linux установлены
- [ ] Backend успешно запустился без ошибок PPTP
- [ ] Тестовый PPTP туннель создается вручную
- [ ] SOCKS5 серверы слушают на портах
- [ ] Прокси файл содержит правильные данные
- [ ] Тест подключения через curl показывает IP узла

## API Endpoints

### POST /api/socks/start
Запуск SOCKS5 + PPTP туннеля
```json
{
  "node_ids": [2, 3, 5],
  "filters": {},
  "masking_settings": {}
}
```

### POST /api/socks/stop
Остановка SOCKS5 + PPTP туннеля
```json
{
  "node_ids": [2, 3, 5],
  "filters": {}
}
```

### GET /api/socks/proxy-file
Получить файл с прокси в формате IP:PORT:LOGIN:PASS

## Контакты

При проблемах проверьте:
1. Логи backend
2. Логи pppd в /tmp/
3. Наличие ppp интерфейсов
4. Capabilities контейнера
