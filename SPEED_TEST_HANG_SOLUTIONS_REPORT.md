# ОТЧЁТ: РЕШЕНИЯ ПРОБЛЕМЫ ЗАВИСАНИЯ ТЕСТА SPEED OK

**Дата:** 2025-01-10  
**Проблема:** Агрессивная дедупликация блокирует тесты на 180 секунд  
**Статус:** Предложены решения

---

## 📋 РЕЗЮМЕ ПРОБЛЕМЫ

**Root Cause:** `TEST_DEDUPE_TTL = 180 секунд` в `/app/backend/server.py` строка 181

**Эффект:** Все узлы пропускаются если тестировались менее 3 минут назад, результат "0 processed" выглядит как зависание.

---

## 🔧 ВАРИАНТЫ РЕШЕНИЯ

### РЕШЕНИЕ 1: УМЕНЬШЕНИЕ TTL (ПРОСТОЕ, БЫСТРОЕ)

**Сложность:** ⭐ Низкая  
**Время:** 1 минута  
**Эффективность:** ⭐⭐⭐ Средняя

#### Что сделать:

**Файл:** `/app/backend/server.py`  
**Строка 181:**

**Было:**
```python
TEST_DEDUPE_TTL = 180  # seconds
```

**Стало (вариант А - агрессивный):**
```python
TEST_DEDUPE_TTL = 30  # seconds - быстрая повторная проверка
```

**Стало (вариант Б - сбалансированный):**
```python
TEST_DEDUPE_TTL = 60  # seconds - баланс между защитой и удобством
```

**Стало (вариант В - минимальный):**
```python
TEST_DEDUPE_TTL = 15  # seconds - только защита от случайных дублей
```

#### Плюсы:
- ✅ Быстро реализуется (1 строка кода)
- ✅ Решает проблему "зависания"
- ✅ Пользователь может быстро перезапустить тест
- ✅ Не ломает существующую логику

#### Минусы:
- ⚠️ Не решает конфликт между PING OK и SPEED OK
- ⚠️ Всё ещё есть задержка (пусть и меньше)
- ⚠️ Нет feedback пользователю о причине блокировки

#### Рекомендация:
**Использовать вариант Б:** `TEST_DEDUPE_TTL = 60`  
60 секунд - разумный компромисс между защитой от спама и удобством пользователя.

---

### РЕШЕНИЕ 2: РАЗДЕЛЬНАЯ ДЕДУПЛИКАЦИЯ ДЛЯ PING И SPEED (ПРАВИЛЬНОЕ)

**Сложность:** ⭐⭐ Средняя  
**Время:** 15-20 минут  
**Эффективность:** ⭐⭐⭐⭐⭐ Высокая

#### Что сделать:

**Концепция:** PING тесты и SPEED тесты должны иметь разные TTL и не блокировать друг друга.

**Файл:** `/app/backend/server.py`

**Шаг 1: Создать раздельные TTL (после строки 181):**

```python
# Было:
TEST_DEDUPE_TTL = 180  # seconds

# Стало:
TEST_DEDUPE_TTL_PING = 60   # seconds - для PING тестов
TEST_DEDUPE_TTL_SPEED = 120  # seconds - для SPEED тестов (дольше, т.к. тяжелее)
TEST_DEDUPE_TTL_DEFAULT = 60 # seconds - для остальных тестов
```

**Шаг 2: Обновить функцию mark_enqueued (строка 194-197):**

**Было:**
```python
def test_dedupe_mark_enqueued(node_id: int, mode: str):
    now = datetime.utcnow().timestamp()
    _test_recent[(node_id, mode)] = now + TEST_DEDUPE_TTL
    _test_inflight.add(node_id)
```

**Стало:**
```python
def test_dedupe_mark_enqueued(node_id: int, mode: str):
    now = datetime.utcnow().timestamp()
    
    # Выбор TTL в зависимости от типа теста
    if mode == "ping":
        ttl = TEST_DEDUPE_TTL_PING
    elif mode == "speed":
        ttl = TEST_DEDUPE_TTL_SPEED
    else:
        ttl = TEST_DEDUPE_TTL_DEFAULT
    
    _test_recent[(node_id, mode)] = now + ttl
    _test_inflight.add(node_id)
```

**Шаг 3: Исправить логику mode_key для ping_speed (строка 3704):**

**Было:**
```python
mode_key = "ping" if testing_mode in ["ping_only", "ping_speed"] else ("speed" if testing_mode in ["speed_only"] else testing_mode)
if test_dedupe_should_skip(node_id, mode_key):
    logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {mode_key})")
    continue
test_dedupe_mark_enqueued(node_id, mode_key)
```

**Стало:**
```python
# Определить какие типы тестов будут выполняться
mode_keys = []
if testing_mode in ["ping_only", "ping_speed"]:
    mode_keys.append("ping")
if testing_mode in ["speed_only", "ping_speed"]:
    mode_keys.append("speed")
if testing_mode not in ["ping_only", "speed_only", "ping_speed"]:
    mode_keys.append(testing_mode)

# Проверить дедупликацию для ВСЕХ типов тестов
should_skip = False
for mode_key in mode_keys:
    if test_dedupe_should_skip(node_id, mode_key):
        logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {mode_key})")
        should_skip = True
        break

if should_skip:
    continue

# Отметить все типы тестов в dedupe
for mode_key in mode_keys:
    test_dedupe_mark_enqueued(node_id, mode_key)
```

#### Плюсы:
- ✅ PING OK не блокирует SPEED OK
- ✅ Разные TTL для разных типов тестов (ping быстрее, speed медленнее)
- ✅ Более гибкая система
- ✅ Правильная обработка режима "ping_speed"

#### Минусы:
- ⚠️ Требует больше изменений в коде
- ⚠️ Всё ещё нет feedback пользователю

#### Рекомендация:
**Это ПРАВИЛЬНОЕ решение** для production системы. Сочетать с РЕШЕНИЕМ 1 и 3.

---

### РЕШЕНИЕ 3: ДОБАВЛЕНИЕ FEEDBACK ДЛЯ ПОЛЬЗОВАТЕЛЯ (ВАЖНОЕ)

**Сложность:** ⭐⭐ Средняя  
**Время:** 10-15 минут  
**Эффективность:** ⭐⭐⭐⭐ Высокая

#### Что сделать:

Пользователь должен **ВИДЕТЬ** почему узлы пропускаются, а не думать что система зависла.

**Файл:** `/app/backend/server.py`

**Шаг 1: Добавить функцию для расчёта оставшегося времени блокировки:**

**Добавить после функции test_dedupe_should_skip (после строки 192):**

```python
def test_dedupe_should_skip(node_id: int, mode: str) -> bool:
    now = datetime.utcnow().timestamp()
    exp = _test_recent.get((node_id, mode))
    if exp and exp > now:
        return True
    if node_id in _test_inflight:
        return True
    return False

# НОВАЯ ФУНКЦИЯ:
def test_dedupe_get_remaining_time(node_id: int, mode: str) -> int:
    """Получить оставшееся время блокировки в секундах"""
    now = datetime.utcnow().timestamp()
    exp = _test_recent.get((node_id, mode))
    if exp and exp > now:
        return int(exp - now)
    return 0
```

**Шаг 2: Обновить сообщение о пропуске (строка 3706-3708):**

**Было:**
```python
if test_dedupe_should_skip(node_id, mode_key):
    logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {mode_key})")
    progress_increment(session_id, f"⏭️ Пропуск {node_id} (повтор {mode_key})")
    continue
```

**Стало:**
```python
if test_dedupe_should_skip(node_id, mode_key):
    remaining = test_dedupe_get_remaining_time(node_id, mode_key)
    logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {mode_key}, wait {remaining}s)")
    progress_increment(session_id, f"⏭️ Узел {node_id} недавно тестировался, подождите {remaining}с")
    continue
```

**Шаг 3: Добавить счётчик пропущенных узлов в итоговую статистику:**

**В конце функции (после строки 3750):**

```python
finally:
    # Complete progress tracking
    if session_id in progress_store:
        # НОВОЕ: Добавить информацию о пропущенных узлах
        skipped_count = total_nodes - processed_nodes - failed_tests
        if skipped_count > 0:
            progress_store[session_id].message = f"Завершено: {processed_nodes} обработано, {failed_tests} ошибок, {skipped_count} пропущено (dedupe)"
        
        progress_store[session_id].complete("completed")
```

#### Плюсы:
- ✅ Пользователь **видит причину** блокировки
- ✅ Показывает оставшееся время ожидания
- ✅ Статистика включает пропущенные узлы
- ✅ Нет путаницы с "зависанием"

#### Минусы:
- ⚠️ Требует изменений в нескольких местах

#### Рекомендация:
**ОБЯЗАТЕЛЬНО** реализовать для лучшего UX.

---

### РЕШЕНИЕ 4: ПАРАМЕТР FORCE_RETEST (ПРОДВИНУТОЕ)

**Сложность:** ⭐⭐⭐ Высокая  
**Время:** 30-40 минут  
**Эффективность:** ⭐⭐⭐⭐⭐ Высокая

#### Что сделать:

Добавить возможность **принудительного** перезапуска теста, игнорируя дедупликацию.

**Файл:** `/app/backend/server.py`

**Шаг 1: Добавить параметр в API endpoints:**

**Найти endpoint для batch progress (примерно строка 3340):**

**Было:**
```python
@api_router.post("/manual/speed-test-batch-progress")
async def speed_test_batch_progress(request: Request, current_user: User = Depends(get_current_user)):
    body = await request.json()
    node_ids = body.get("node_ids", [])
    # ...
```

**Стало:**
```python
@api_router.post("/manual/speed-test-batch-progress")
async def speed_test_batch_progress(request: Request, current_user: User = Depends(get_current_user)):
    body = await request.json()
    node_ids = body.get("node_ids", [])
    force_retest = body.get("force_retest", False)  # НОВЫЙ ПАРАМЕТР
    # ...
```

**Шаг 2: Передать параметр в testing batch функцию:**

```python
# Запуск тестирования в фоне
asyncio.create_task(testing_batch(
    session_id, node_ids, testing_mode="speed_only",
    force_retest=force_retest  # ПЕРЕДАТЬ ПАРАМЕТР
))
```

**Шаг 3: Обновить функцию testing_batch (добавить параметр):**

**Найти определение функции testing_batch (примерно строка 3520):**

**Было:**
```python
async def testing_batch(session_id: str, node_ids: List[int], testing_mode: str = "ping_speed", ...):
```

**Стало:**
```python
async def testing_batch(session_id: str, node_ids: List[int], testing_mode: str = "ping_speed", 
                       force_retest: bool = False, ...):
```

**Шаг 4: Обновить проверку dedupe (строка 3705-3708):**

**Было:**
```python
if test_dedupe_should_skip(node_id, mode_key):
    logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {mode_key})")
    continue
```

**Стало:**
```python
if not force_retest and test_dedupe_should_skip(node_id, mode_key):
    remaining = test_dedupe_get_remaining_time(node_id, mode_key)
    logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {mode_key}, wait {remaining}s)")
    progress_increment(session_id, f"⏭️ Узел {node_id} пропущен (подождите {remaining}с или используйте force_retest)")
    continue
```

**Шаг 5: Добавить UI элемент в Frontend:**

**Файл:** `/app/frontend/src/components/TestingModal.js`

Добавить чекбокс "Принудительный перезапуск (игнорировать dedupe)" перед кнопками запуска тестов.

```javascript
<div className="flex items-center mb-4">
  <input 
    type="checkbox" 
    id="forceRetest"
    checked={forceRetest}
    onChange={(e) => setForceRetest(e.target.checked)}
    className="mr-2"
  />
  <label htmlFor="forceRetest" className="text-sm">
    ⚡ Принудительный перезапуск (игнорировать dedupe)
  </label>
</div>
```

#### Плюсы:
- ✅ Админ может **принудительно** перезапустить любой тест
- ✅ Гибкость для диагностики и отладки
- ✅ Не отключает защиту по умолчанию
- ✅ Удобно для testing и development

#### Минусы:
- ⚠️ Требует изменений в backend и frontend
- ⚠️ Может быть использован для спама (но это админ)

#### Рекомендация:
**Опциональное** решение для продвинутых пользователей и отладки.

---

### РЕШЕНИЕ 5: ВРЕМЕННОЕ ОТКЛЮЧЕНИЕ DEDUPE (АВАРИЙНОЕ)

**Сложность:** ⭐ Очень низкая  
**Время:** 10 секунд  
**Эффективность:** ⭐⭐ Низкая (только для отладки)

#### Что сделать:

**Файл:** `/app/backend/server.py`  
**Строка 181:**

```python
# ВРЕМЕННО: Отключить dedupe для диагностики
TEST_DEDUPE_TTL = 0  # seconds - dedupe отключен
```

ИЛИ

**Строка 185-192:**

```python
def test_dedupe_should_skip(node_id: int, mode: str) -> bool:
    # ВРЕМЕННО: Всегда возвращать False (dedupe отключен)
    return False
    
    # Закомментировать остальное:
    # now = datetime.utcnow().timestamp()
    # exp = _test_recent.get((node_id, mode))
    # ...
```

#### Плюсы:
- ✅ Мгновенно решает проблему зависания
- ✅ Позволяет тестировать без ограничений

#### Минусы:
- ❌ **НЕ РЕКОМЕНДУЕТСЯ** для production
- ❌ Нет защиты от случайных дублей
- ❌ Может перегрузить систему при частых запусках

#### Рекомендация:
**ТОЛЬКО для отладки и диагностики.** Не использовать в production.

---

## 📊 СРАВНИТЕЛЬНАЯ ТАБЛИЦА РЕШЕНИЙ

| Решение | Сложность | Время | Эффективность | Production Ready | Рекомендация |
|---------|-----------|-------|---------------|------------------|--------------|
| 1. Уменьшение TTL | ⭐ | 1 мин | ⭐⭐⭐ | ✅ | ✅ СДЕЛАТЬ СРАЗУ |
| 2. Раздельная dedupe | ⭐⭐ | 15-20 мин | ⭐⭐⭐⭐⭐ | ✅ | ✅ ПРАВИЛЬНОЕ |
| 3. Feedback пользователю | ⭐⭐ | 10-15 мин | ⭐⭐⭐⭐ | ✅ | ✅ ОБЯЗАТЕЛЬНО |
| 4. Force retest | ⭐⭐⭐ | 30-40 мин | ⭐⭐⭐⭐⭐ | ✅ | ⚠️ ОПЦИОНАЛЬНО |
| 5. Отключение dedupe | ⭐ | 10 сек | ⭐⭐ | ❌ | ❌ ТОЛЬКО DEBUG |

---

## 🎯 РЕКОМЕНДУЕМЫЙ ПЛАН ДЕЙСТВИЙ

### ЭТАП 1: БЫСТРОЕ ИСПРАВЛЕНИЕ (5 минут)

**Цель:** Убрать эффект "зависания" немедленно

1. ✅ **Уменьшить TTL** (РЕШЕНИЕ 1)
   - Изменить `TEST_DEDUPE_TTL = 180` → `TEST_DEDUPE_TTL = 60`
   - Перезапустить backend: `sudo supervisorctl restart backend`
   - Проверить работу

**Результат:** Пользователи могут перезапускать тесты каждую минуту вместо каждые 3 минуты.

---

### ЭТАП 2: ПРАВИЛЬНОЕ ИСПРАВЛЕНИЕ (30 минут)

**Цель:** Разделить PING и SPEED дедупликацию

1. ✅ **Раздельная дедупликация** (РЕШЕНИЕ 2)
   - Создать `TEST_DEDUPE_TTL_PING` и `TEST_DEDUPE_TTL_SPEED`
   - Обновить `test_dedupe_mark_enqueued()`
   - Исправить логику `mode_key` для режима `ping_speed`

2. ✅ **Добавить feedback** (РЕШЕНИЕ 3)
   - Добавить `test_dedupe_get_remaining_time()`
   - Обновить сообщения о пропуске
   - Показать статистику пропущенных узлов

**Результат:** PING OK не блокирует SPEED OK, пользователь видит причину блокировки.

---

### ЭТАП 3: ПРОДВИНУТЫЕ ФУНКЦИИ (опционально, 40 минут)

**Цель:** Добавить гибкость для админов

1. ⚠️ **Force retest параметр** (РЕШЕНИЕ 4)
   - Добавить `force_retest` в API
   - Обновить UI с чекбоксом
   - Обновить логику проверки dedupe

**Результат:** Админ может принудительно перезапустить любой тест.

---

## 🔍 ПРИМЕРЫ КОДА ДЛЯ КАЖДОГО РЕШЕНИЯ

### РЕШЕНИЕ 1: Код для уменьшения TTL

**Файл:** `/app/backend/server.py`  
**Строка:** 181

```python
# БЫЛО:
TEST_DEDUPE_TTL = 180  # seconds

# СТАЛО (рекомендация):
TEST_DEDUPE_TTL = 60  # seconds - баланс между защитой и удобством

# Альтернативы:
# TEST_DEDUPE_TTL = 30  # более агрессивное
# TEST_DEDUPE_TTL = 15  # только защита от случайных дублей
```

---

### РЕШЕНИЕ 2: Код для раздельной дедупликации

**Файл:** `/app/backend/server.py`

**Изменение 1 (после строки 181):**

```python
# СТАРЫЙ КОД:
TEST_DEDUPE_TTL = 180  # seconds

# НОВЫЙ КОД:
TEST_DEDUPE_TTL_PING = 60   # seconds - для PING тестов (быстрее)
TEST_DEDUPE_TTL_SPEED = 120  # seconds - для SPEED тестов (медленнее, тяжелее)
TEST_DEDUPE_TTL_DEFAULT = 60 # seconds - для остальных
```

**Изменение 2 (строки 194-197):**

```python
# СТАРЫЙ КОД:
def test_dedupe_mark_enqueued(node_id: int, mode: str):
    now = datetime.utcnow().timestamp()
    _test_recent[(node_id, mode)] = now + TEST_DEDUPE_TTL
    _test_inflight.add(node_id)

# НОВЫЙ КОД:
def test_dedupe_mark_enqueued(node_id: int, mode: str):
    now = datetime.utcnow().timestamp()
    
    # Выбор TTL в зависимости от типа теста
    if mode == "ping":
        ttl = TEST_DEDUPE_TTL_PING
    elif mode == "speed":
        ttl = TEST_DEDUPE_TTL_SPEED
    else:
        ttl = TEST_DEDUPE_TTL_DEFAULT
    
    _test_recent[(node_id, mode)] = now + ttl
    _test_inflight.add(node_id)
```

**Изменение 3 (строки 3704-3710):**

```python
# СТАРЫЙ КОД:
mode_key = "ping" if testing_mode in ["ping_only", "ping_speed"] else ("speed" if testing_mode in ["speed_only"] else testing_mode)
if test_dedupe_should_skip(node_id, mode_key):
    logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {mode_key})")
    continue
test_dedupe_mark_enqueued(node_id, mode_key)

# НОВЫЙ КОД:
# Определить какие типы тестов будут выполняться
mode_keys = []
if testing_mode in ["ping_only", "ping_speed"]:
    mode_keys.append("ping")
if testing_mode in ["speed_only", "ping_speed"]:
    mode_keys.append("speed")
if not mode_keys:  # Для остальных режимов
    mode_keys.append(testing_mode)

# Проверить дедупликацию для ВСЕХ типов тестов
should_skip = False
skip_reason = ""
for mode_key in mode_keys:
    if test_dedupe_should_skip(node_id, mode_key):
        skip_reason = mode_key
        should_skip = True
        break

if should_skip:
    logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {skip_reason})")
    progress_increment(session_id, f"⏭️ Пропуск {node_id} (повтор {skip_reason})")
    continue

# Отметить все типы тестов в dedupe
for mode_key in mode_keys:
    test_dedupe_mark_enqueued(node_id, mode_key)
```

---

### РЕШЕНИЕ 3: Код для feedback пользователю

**Файл:** `/app/backend/server.py`

**Изменение 1 (после строки 192, добавить новую функцию):**

```python
def test_dedupe_should_skip(node_id: int, mode: str) -> bool:
    now = datetime.utcnow().timestamp()
    exp = _test_recent.get((node_id, mode))
    if exp and exp > now:
        return True
    if node_id in _test_inflight:
        return True
    return False

# НОВАЯ ФУНКЦИЯ:
def test_dedupe_get_remaining_time(node_id: int, mode: str) -> int:
    """Получить оставшееся время блокировки в секундах"""
    now = datetime.utcnow().timestamp()
    exp = _test_recent.get((node_id, mode))
    if exp and exp > now:
        return int(exp - now)
    return 0
```

**Изменение 2 (обновить сообщения о пропуске):**

```python
# СТАРЫЙ КОД (строка 3706):
if test_dedupe_should_skip(node_id, mode_key):
    logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {mode_key})")
    progress_increment(session_id, f"⏭️ Пропуск {node_id} (повтор {mode_key})")
    continue

# НОВЫЙ КОД:
if test_dedupe_should_skip(node_id, mode_key):
    remaining = test_dedupe_get_remaining_time(node_id, mode_key)
    logger.info(f"⏭️ Testing: Skipping node {node_id} (dedupe {mode_key}, wait {remaining}s)")
    progress_increment(session_id, f"⏭️ Узел {node_id} недавно тестировался, подождите {remaining}с")
    continue
```

---

## 📌 ЗАКЛЮЧЕНИЕ

### Минимальное решение (СЕЙЧАС):
```python
# /app/backend/server.py строка 181
TEST_DEDUPE_TTL = 60  # было 180
```
+ **Перезапуск:** `sudo supervisorctl restart backend`

### Полное решение (РЕКОМЕНДУЕТСЯ):
1. Раздельные TTL для ping/speed (РЕШЕНИЕ 2)
2. Feedback пользователю (РЕШЕНИЕ 3)
3. Уменьшенный TTL (РЕШЕНИЕ 1)

### Время реализации:
- Быстрое: 1 минута
- Полное: 30-40 минут

### Результат:
- ✅ Нет "зависания"
- ✅ PING OK не блокирует SPEED OK
- ✅ Пользователь видит причину блокировки
- ✅ Production ready решение

---

**Все изменения документированы** и готовы к реализации.
