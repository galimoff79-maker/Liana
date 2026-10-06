# ПриватЧат — Приватный мессенджер для двоих

Полноценный приватный веб-мессенджер для общения двух пользователей. Поддержка iPhone, Android и Windows. PWA с push-уведомлениями.

---

## 📋 Возможности

### Основной функционал
- ✅ Регистрация / Вход / Logout
- ✅ Invite-система (только 2 пользователя)
- ✅ Текстовые сообщения с emoji
- ✅ Ответы (reply) на сообщения
- ✅ Редактирование сообщений
- ✅ Удаление (у себя / у обоих)
- ✅ Реакции (❤️ 👍 😂 😮 😢 🔥 🎉)
- ✅ Закрепление сообщений
- ✅ Статусы: отправлено ✓ / доставлено ✓✓ / прочитано ✓✓
- ✅ Индикатор "печатает..."
- ✅ Online / Offline статус
- ✅ Поиск по истории

### Медиа
- ✅ Отправка фотографий (с preview)
- ✅ Отправка видео (с встроенным плеером)
- ✅ Отправка файлов (PDF, DOC, ZIP и др.)
- ✅ Голосовые сообщения
- ✅ Камера (мобильные устройства)
- ✅ Полноэкранный просмотр изображений с zoom
- ✅ Скачивание файлов

### PWA и Push
- ✅ Progressive Web App
- ✅ Установка на домашний экран (iPhone/Android)
- ✅ Push-уведомления (Web Push + VAPID)
- ✅ Service Worker с кэшированием
- ✅ Standalone mode

### Безопасность
- ✅ HTTPS (Let's Encrypt)
- ✅ Безопасное хэширование паролей (bcrypt)
- ✅ JWT токены
- ✅ Защита от CSRF, XSS, SQL injection
- ✅ Rate limiting
- ✅ Security headers (CSP, HSTS, X-Frame-Options)
- ✅ Файлы не публичны — проверка прав доступа
- ✅ Случайные имена загружаемых файлов
- ✅ Защита от path traversal

### Интерфейс
- ✅ Dark / Light / System тема
- ✅ Responsive дизайн (mobile-first)
- ✅ Оптимизация под iPhone (Safe Area, Dynamic Island)
- ✅ Корректная работа с виртуальной клавиатурой
- ✅ Современный UI в стиле мессенджера

### Инфраструктура
- ✅ Docker + Docker Compose
- ✅ PostgreSQL
- ✅ Nginx (reverse proxy)
- ✅ WebSocket (real-time)
- ✅ Автоматическое удаление старых файлов
- ✅ Backup / Restore скрипты

---

## 🚀 Быстрый запуск (Development)

### Требования
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (или Docker)

### 1. Клонирование
```bash
git clone <repository-url>
cd privatchat
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Настроить .env
cp ../.env.example .env
# Отредактировать .env

# Запустить
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend
```bash
cd frontend  # (или корень проекта)
npm install
npm run dev
```

### 4. Открыть
```
http://localhost:3000
```

---

## 🐳 Docker (Production)

### 1. Подготовка
```bash
cp .env.example .env
```

Отредактировать `.env`:
```env
SECRET_KEY=<сгенерировать: python -c "import secrets; print(secrets.token_urlsafe(64))">
DB_PASSWORD=<надёжный_пароль>
FRONTEND_URL=https://chat.example.com
DOMAIN=chat.example.com
```

### 2. Запуск
```bash
docker compose up -d
```

### 3. Проверка
```bash
docker compose ps
docker compose logs -f backend
```

---

## 🌐 Настройка домена и HTTPS

### 1. DNS
Направить A-запись `chat.example.com` на IP вашего VPS.

### 2. Let's Encrypt
```bash
# Установить certbot
apt install certbot

# Получить сертификат
certbot certonly --standalone -d chat.example.com

# Скопировать в nginx
cp /etc/letsencrypt/live/chat.example.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/chat.example.com/privkey.pem nginx/ssl/
```

### 3. Включить HTTPS в nginx.conf
Раскомментировать блок HTTPS в `nginx/nginx.conf` и перезапустить:
```bash
docker compose restart nginx
```

### 4. Автоматическое обновление
```bash
# Добавить в crontab
0 0 1 * * certbot renew --quiet && docker compose restart nginx
```

---

## 📱 Установка на iPhone

1. Открыть Safari → `https://chat.example.com`
2. Зарегистрироваться / Войти
3. Нажать кнопку «Поделиться» (⬆️)
4. Выбрать «На экран «Домой»»
5. Подтвердить

Приложение откроется в полноэкранном режиме без адресной строки.

### Push-уведомления на iPhone
- Требуется iOS 16.4+
- После добавления на экран: Настройки → ПриватЧат → Уведомления → Разрешить
- Приложение запросит разрешение при первом входе

---

## 📱 Установка на Android

1. Открыть Chrome → `https://chat.example.com`
2. Зарегистрироваться / Войти
3. Chrome предложит «Добавить на главный экран»
4. Или: меню (⋮) → «Установить приложение»

---

## 💻 Windows

Просто открыть в браузере:
```
https://chat.example.com
```

Поддерживаются: Chrome, Edge, Firefox.

Для установки как приложение:
- Chrome: адресная строка → иконка установки
- Edge: меню → Приложения → Установить этот сайт как приложение

---

## 🔔 Push-уведомления

### Генерация VAPID ключей
```bash
npx web-push generate-vapid-keys
```

Добавить в `.env`:
```env
VAPID_PUBLIC_KEY=<public_key>
VAPID_PRIVATE_KEY=<private_key>
```

---

## 💾 Backup / Restore

### Linux/Mac
```bash
# Backup
chmod +x scripts/backup.sh
./scripts/backup.sh

# Restore
chmod +x scripts/restore.sh
./scripts/restore.sh privatchat_backup_20240101_120000
```

### Windows
```powershell
# Backup
.\scripts\backup.ps1

# Restore
.\scripts\restore.ps1 -BackupName "privatchat_backup_20240101_120000"
```

---

## 🏗 Структура проекта

```
privatchat/
├── backend/
│   ├── app/
│   │   └── main.py          # FastAPI приложение
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # (корень проекта)
│   ├── src/
│   │   ├── App.tsx           # Главный компонент
│   │   ├── main.tsx          # Точка входа
│   │   ├── index.css         # Стили
│   │   ├── types/index.ts    # TypeScript типы
│   │   ├── stores/index.ts   # Zustand store
│   │   └── components/
│   │       ├── AuthScreen.tsx
│   │       ├── ChatView.tsx
│   │       ├── MessageBubble.tsx
│   │       ├── SettingsView.tsx
│   │       └── MediaViewer.tsx
│   ├── public/
│   │   ├── manifest.json     # PWA manifest
│   │   └── sw.js             # Service Worker
│   ├── Dockerfile
│   └── index.html
├── nginx/
│   └── nginx.conf
├── scripts/
│   ├── backup.sh
│   ├── restore.sh
│   ├── backup.ps1
│   └── restore.ps1
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔧 Environment Variables

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `SECRET_KEY` | JWT secret (обязательно менять!) | random |
| `DB_PASSWORD` | Пароль PostgreSQL | `privatchat_secret` |
| `VAPID_PUBLIC_KEY` | VAPID public key для push | — |
| `VAPID_PRIVATE_KEY` | VAPID private key для push | — |
| `UPLOAD_DIR` | Директория для файлов | `./uploads` |
| `FILE_RETENTION_DAYS` | Хранение файлов (дни) | `30` |
| `MAX_FILE_SIZE_MB` | Макс. размер файла | `500` |
| `FRONTEND_URL` | URL фронтенда | `http://localhost:3000` |

---

## 🗄 Database

### Таблицы
- `users` — пользователи
- `sessions` — сессии/токены
- `messages` — сообщения
- `attachments` — вложения
- `invites` — коды-приглашения
- `push_subscriptions` — push подписки

### Миграции (Alembic)
```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## 🔒 Безопасность

### Реализовано
- HTTPS (обязательно для production)
- Secure cookies (HttpOnly, SameSite, Secure)
- CSRF protection
- XSS protection (React по умолчанию + CSP)
- SQL injection protection (SQLAlchemy ORM)
- Rate limiting
- Brute-force protection
- Безопасное хэширование паролей (bcrypt)
- Security headers
- Content Security Policy
- CORS
- WebSocket authentication (JWT)
- Проверка прав доступа к файлам
- Проверка размера файлов
- Проверка MIME типов
- Защита от path traversal
- Случайные имена файлов
- Запрет исполнения загруженных файлов

### Рекомендации
- Менять `SECRET_KEY` перед production
- Использовать надёжный пароль для PostgreSQL
- Обновлять сертификаты Let's Encrypt
- Регулярно делать backup
- Обновлять зависимости

---

## 📋 Известные ограничения браузеров

### iOS Safari
- Web Push работает только после добавления PWA на домашний экран (iOS 16.4+)
- MediaRecorder имеет ограниченную поддержку (iOS 14.3+)
- Нет фоновой работы WebSocket (при сворачивании)
- Ограничение на размер загружаемых файлов (~500MB)

### Android Chrome
- Полная поддержка всех функций
- Push работает без ограничений

### Desktop (Chrome/Edge/Firefox)
- Полная поддержка всех функций
- Push работает через Service Worker

---

## 🔮 Планируемые улучшения (v2)

- End-to-End Encryption (E2EE)
- Голосовые звонки (WebRTC)
- Видеозвонки
- Групповые чаты
- Несколько чатов
- Стикерпаки
- GIF поиск
- Исчезающие сообщения
- Двухфакторная аутентификация
- Экспорт истории чата

---

## 📄 Лицензия

Private use only.
