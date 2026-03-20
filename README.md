# AutoPilot Pro 🔧

**Production-ready Telegram SaaS-бот для автосервисов**

---

## Быстрый старт

### 1. Клонировать и настроить окружение

```bash
cp .env.example .env
# Заполнить все переменные в .env
```

### 2. Запустить локально

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

### 3. Для локального тестирования бота — ngrok

```bash
ngrok http 8080
# Скопировать https-URL → вставить в WEBHOOK_URL в .env
# Перезапустить uvicorn
```

---

## Деплой на Railway

1. Создать новый проект на [railway.app](https://railway.app)
2. Подключить этот GitHub репозиторий
3. Добавить переменные окружения:

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен от @BotFather |
| `DATABASE_URL` | PostgreSQL URL (напр. Supabase) |
| `OPENAI_API_KEY` | Ключ OpenAI |
| `WEBHOOK_URL` | URL вашего Railway-деплоя |
| `SECRET_TOKEN` | Любая случайная строка |

Railway автоматически найдёт `Dockerfile` и задеплоит.

---

## Архитектура

```
app/
├── main.py              # FastAPI + webhook endpoint
├── config.py            # Настройки из .env
├── database.py          # SQLAlchemy engine
├── models/              # БД модели (Shop, User, Estimate...)
├── handlers/
│   ├── start.py         # /start + deep link + /newshop
│   ├── admin.py         # Все admin:* callbacks
│   └── worker.py        # Обработка текста/голоса + PDF
├── services/
│   ├── ai_service.py    # OpenAI Whisper + GPT-4o
│   ├── pricing_service.py  # Матчинг цен + форматирование сметы
│   └── pdf_service.py   # ReportLab PDF генерация
├── middlewares/
│   └── shop_context.py  # Инъекция user/shop/membership в handlers
├── keyboards/           # Inline и Reply клавиатуры
└── states/              # FSM состояния (aiogram)
```

---

## User flow

### Новый автосервис
1. Получить ссылку: `https://t.me/YourBot?start=MYSHOP`
2. Первый кто зашёл → становится **Admin**
3. Остальные → **Worker**
4. Или создать сервис командой `/newshop`

### Механик (Worker)
1. Отправить голос/текст: _"Тойота Камри 2020, масло и фильтр, передние колодки"_
2. Бот анализирует → составляет смету с ценами из прайса
3. Нажать **✅ Подтвердить и PDF** → получить PDF документ

### Администратор
- `⚙️ Админ панель` → меню управления
- Добавить цены на работы вручную
- Загрузить прайс запчастей (CSV/Excel)
- Загрузить логотип
- Настроить название, город, телефон
- Просмотреть историю смет
- Пригласить сотрудников

---

## Формат CSV для запчастей

```csv
name,price,brand,part_number
Масло моторное 5W-40 4л,4500,Mobil,MBL-5W40-4
Фильтр масляный,800,Mahle,OC217
Тормозные колодки передние,3200,Brembo,P85020
```

---

## База данных

| Таблица | Описание |
|---------|----------|
| `shops` | Автосервисы (мультитенант) |
| `users` | Telegram пользователи |
| `memberships` | Связь user↔shop + роль |
| `subscriptions` | Подписка (trial/basic/pro) |
| `labor_prices` | Прайс на работы |
| `part_prices` | Прайс на запчасти |
| `estimates` | Сметы |
| `estimate_items` | Позиции сметы |
