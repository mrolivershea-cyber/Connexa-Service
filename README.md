# Connexa Admin Panel v7.0

PPTP/SOCKS5/OpenVPN администрирование и мониторинг.

## 🚀 Быстрая установка (одна команда)

```bash
curl -fsSL https://raw.githubusercontent.com/mrolivershea-cyber/Connexa-/main/universal_install.sh | sudo bash
```

## 📋 Требования

- Ubuntu 20.04+ / Debian 11+
- Root доступ
- 2GB RAM minimum
- 10GB свободного места

## ✨ Возможности v7.0

- ✅ Управление PPTP/SOCKS5/OpenVPN узлами
- ✅ Тесты: Ping Light, Ping OK, Speed, GEO, Fraud, GEO+Fraud
- ✅ **НОВОЕ:** Координаты (широта/долгота) в тестах
- ✅ **НОВОЕ:** Цветная схема Risk Level (LOW/MEDIUM/HIGH/CRITICAL)
- ✅ **ИСПРАВЛЕНО:** Результаты тестов ГЕО/Фрауд работают корректно
- ✅ Импорт из файлов (множество форматов)
- ✅ Экспорт конфигураций (PPTP/SOCKS5/OpenVPN)
- ✅ Автоматический мониторинг узлов

## 🔐 Доступ после установки

- Frontend: `http://YOUR_SERVER_IP:3000`
- Backend: `http://YOUR_SERVER_IP:8001`
- Логин: `admin`
- Пароль: `admin`

## 📝 Управление

```bash
# Статус сервисов
sudo supervisorctl status

# Перезапуск
sudo supervisorctl restart all

# Логи
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/frontend.out.log
```

## 🔧 Конфигурация

### Backend (.env)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
IPQS_API_KEY="your_api_key_here"
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 📊 API Ключи

- **IPQualityScore**: Для fraud detection (опционально)
- Бесплатные API: ip-api.com для геолокации

## 🆘 Поддержка

При проблемах проверьте логи:
```bash
tail -f /var/log/supervisor/backend.err.log
```

---

**Версия 7.0** - Final Release with Coordinates & Test Fixes
