# 🚀 CONNEXA ADMIN PANEL - UPGRADED VERSION

**Улучшенная версия системы управления PPTP/VPN узлами с расширенными фильтрами и Scamalytics интеграцией**

---

## ✨ ЧТО НОВОГО В ЭТОЙ ВЕРСИИ:

### **1. Исправлены критические проблемы фильтров** ✅
- Исправлены конфликты импортов (`@/` → `../`)
- Устранен Race Condition (двойная загрузка данных)
- Все 15 фильтров работают корректно

### **2. Супер-гибкий парсер данных** ✅
- **14 вариаций формата Location** - работает с любыми изменениями
- Поддерживает: запятые, точки, двоеточия, пробелы, скобки
- Примеры: `US (Washington, Mill Creek)`, `Germany (Hesse, Frankfurt)`, `Texas (Austin)`

### **3. Scamalytics интеграция** ✅
- Fraud Score (0-100) - показывает репутацию IP
- Risk Level (Low/Medium/High) - уровень риска
- Автоматический импорт из логов

### **4. Расширенные фильтры** ✅
- **Speed фильтры:** speed_min, speed_max (для результатов speed тестов)
- **Scamalytics фильтры:** fraud_score_min, fraud_score_max, risk level
- Все фильтры работают с Select All режимом

### **5. Улучшенная производительность** ✅
- Chunked import для больших файлов (>500KB)
- Скорость парсинга: **31,622 узла/сек**
- Прогресс в реальном времени

---

## 📦 БЫСТРАЯ УСТАНОВКА

### **ONE-COMMAND INSTALL:**

```bash
curl -sSL https://raw.githubusercontent.com/mrolivershea-cyber/Connexa-UPGRATE/main/INSTALL_UPGRADED.sh | bash
```

### **ИЛИ ВРУЧНУЮ:**

```bash
# 1. Клонировать репозиторий
git clone https://github.com/mrolivershea-cyber/Connexa-UPGRATE.git
cd Connexa-UPGRATE

# 2. Запустить установку
bash INSTALL_UPGRADED.sh
```

---

## 🔧 РУЧНАЯ УСТАНОВКА (если нужно):

### **Backend:**

```bash
cd backend

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
cat > .env << 'EOF'
SECRET_KEY=connexa-secret-key-change-in-production
DATABASE_URL=sqlite:///./connexa.db
CORS_ORIGINS=*
EOF

# Запустить
uvicorn server:app --host 0.0.0.0 --port 8001
```

### **Frontend:**

```bash
cd frontend

# Установить зависимости
yarn install

# Создать .env файл
cat > .env << 'EOF'
REACT_APP_BACKEND_URL=http://localhost:8001/api
EOF

# Для разработки
yarn start

# Для production
yarn build
```

---

## 🔐 ДОСТУП ПО УМОЛЧАНИЮ:

```
Username: admin
Password: admin
```

**⚠️ ВАЖНО: Смените пароль после первого входа!**

---

## 🌐 URLS:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001/api
- **API Документация:** http://localhost:8001/docs
- **Health Check:** http://localhost:8001/health

---

## 📋 ПОДДЕРЖИВАЕМЫЕ ФОРМАТЫ ИМПОРТА:

### **Format 1: Key-Value**
```
Ip: 192.168.1.1
Login: admin
Pass: password
State: California
City: Los Angeles
Zip: 90001
```

### **Format 2: Space-separated**
```
192.168.1.1 admin password California
```

### **Format 3: Dash-separated**
```
192.168.1.1 - admin:password - California/Los Angeles 90001
```

### **Format 4: Colon-separated**
```
192.168.1.1:admin:password:United States:California:90001
```

### **Format 5: Multi-line (основной)**
```
IP: 192.168.1.1
Credentials: admin:password
Location: US (California, Los Angeles)
ZIP: 90001
Scamalytics Fraud Score: 35
Scamalytics Risk: medium
```

### **Format 6: With PPTP header (основной с заголовком)**
```
> PPTP_SVOIM_VPN:
🚨 PPTP Connection
IP: 192.168.1.1
Credentials: admin:password
Location: Texas (Austin)
ZIP: 78701
Scamalytics Fraud Score: 15
Scamalytics Risk: low
```

### **Format 7: Simple**
```
192.168.1.1:admin:password
```

---

## 🔍 ДОСТУПНЫЕ ФИЛЬТРЫ:

### **Базовые фильтры:**
- IP Address, Provider, Country, State, City, ZIP Code
- Login, Comment

### **Dropdown фильтры:**
- **Status:** Not Tested, PING LIGHT, PING Failed, PING OK, Speed OK, Online
- **Protocol:** PPTP, SSH, SOCKS, SERVER

### **Числовые фильтры:**
- **Speed Min/Max:** Фильтрация по скорости (Mbps)
- **Fraud Score Min/Max:** Фильтрация по Scamalytics fraud score (0-100)
- **Scam Risk:** Low, Medium, High, Critical

---

## 📊 ВОЗМОЖНОСТИ:

- ✅ **Импорт узлов** - 7 форматов, chunked для больших файлов
- ✅ **Тестирование** - PING LIGHT, Speed Test, Combined
- ✅ **SOCKS управление** - запуск/остановка SOCKS5 прокси
- ✅ **Экспорт данных** - CSV, JSON, TXT
- ✅ **Bulk операции** - массовое удаление, тестирование
- ✅ **Select All** - выбор всех узлов с фильтрами
- ✅ **Real-time прогресс** - для импорта и тестирования
- ✅ **Статистика** - в реальном времени

---

## 🛠️ ТЕХНОЛОГИЧЕСКИЙ СТЕК:

- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** React.js
- **Database:** SQLite
- **UI:** Tailwind CSS + Shadcn/ui

---

## 📝 ОСНОВНЫЕ ОТЛИЧИЯ ОТ СТАРЫХ ВЕРСИЙ:

### **vs SERVICE (старая версия):**
- ✅ Добавлены Scamalytics поля
- ✅ Улучшен парсер Location (2 формата → 14 форматов)
- ✅ Добавлены Speed фильтры
- ✅ Исправлена функция копирования

### **vs 10-23-2025-auto-pars-filter1 (сломанная):**
- ✅ Исправлены импорты (`@/` → `../`)
- ✅ Устранен Race Condition
- ✅ Исправлена функция copySocks
- ✅ Добавлена поддержка фильтров в backend
- ✅ Обновлены зависимости (pydantic 2.12.3, fastapi 0.115.0)

---

## 🧪 ТЕСТИРОВАНИЕ:

**Протестировано на:**
- ✅ 6,419 узлов из реального файла PPTP.txt (753KB)
- ✅ 100% успех парсинга
- ✅ Скорость: 31,622 узла/сек
- ✅ Chunked import: 2.5 секунды для 753KB

---

## 📞 ПОДДЕРЖКА:

**Issues:** https://github.com/mrolivershea-cyber/Connexa-UPGRATE/issues

---

## 📜 ЛИЦЕНЗИЯ:

MIT License - используйте свободно

---

## 🎯 CHANGELOG:

### **v2.0 (Upgraded) - 2025-10-25**

**Fixed:**
- Импорты компонентов (relative paths)
- Race condition в фильтрах
- Функция copyToClipboard (совместимость)
- Функция copySocks (правильные поля)
- Backend поддержка всех фильтров

**Added:**
- Супер-гибкий парсер Location (14 форматов)
- Speed фильтры (min/max)
- Scamalytics фильтры (fraud score, risk)
- Scamalytics колонки в таблице
- parse_location_smart() функция

**Improved:**
- Производительность парсинга (31K узлов/сек)
- Устойчивость к изменениям формата
- Chunked import для больших файлов

---

**Made with ❤️ for PPTP/VPN Management**
