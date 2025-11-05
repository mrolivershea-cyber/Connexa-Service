# 🚀 КОМАНДА ДЛЯ УСТАНОВКИ CONNEXA UPGRADED

## 💾 УСТАНОВКА НА СЕРВЕР - ONE COMMAND:

```bash
curl -sSL https://raw.githubusercontent.com/mrolivershea-cyber/Connexa-UPGRATE/main/universal_install.sh | sudo bash
```

---

## ⚡ ЧТО ДЕЛАЕТ КОМАНДА:

1. ✅ Загружает установочный скрипт из GitHub
2. ✅ Устанавливает все зависимости (Python, Node.js, Yarn)
3. ✅ Клонирует репозиторий Connexa-UPGRATE
4. ✅ Настраивает backend и frontend
5. ✅ Создает базу данных
6. ✅ Настраивает Supervisor
7. ✅ Настраивает Nginx (если нужно)
8. ✅ Запускает сервисы

---

## 📋 ТРЕБОВАНИЯ:

- ✅ Ubuntu/Debian сервер (18.04+)
- ✅ Root доступ (sudo)
- ✅ Интернет соединение
- ✅ Свободно: ~500MB места, 512MB RAM

---

## 🔐 ДОСТУП ПОСЛЕ УСТАНОВКИ:

```
URL: http://ВАШ_IP_СЕРВЕРА
Username: admin
Password: admin
```

⚠️ **ОБЯЗАТЕЛЬНО смените пароль после входа!**

---

## 🔍 ПРОВЕРКА УСТАНОВКИ:

```bash
# Проверить статус сервисов
sudo supervisorctl status

# Проверить backend
curl http://localhost:8001/health

# Проверить логи
tail -f /var/log/connexa-backend.out.log
```

---

## 🛠️ УПРАВЛЕНИЕ:

```bash
# Перезапуск
sudo supervisorctl restart connexa-backend connexa-frontend

# Остановка
sudo supervisorctl stop connexa-backend connexa-frontend

# Запуск
sudo supervisorctl start connexa-backend connexa-frontend
```

---

## ✨ ЧТО ВКЛЮЧЕНО:

- ✅ **15 рабочих фильтров** (IP, Status, Speed, Scamalytics)
- ✅ **Супер-гибкий парсер** (14 форматов Location)
- ✅ **Scamalytics интеграция** (Fraud Score + Risk)
- ✅ **7 форматов импорта** данных
- ✅ **Chunked import** для больших файлов (>500KB)
- ✅ **Real-time прогресс** для всех операций

---

## 📞 ПОДДЕРЖКА:

**Issues:** https://github.com/mrolivershea-cyber/Connexa-UPGRATE/issues

---

**Версия:** 6.0 Upgraded  
**Дата:** 2025-10-25
