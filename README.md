# Liana — Приватный мессенджер для двоих

Production-ready приватный веб-мессенджер для двух пользователей. Поддержка iPhone, Android, Windows. PWA с push-уведомлениями.

---

## ✅ Реализованные возможности

### Основной функционал
- ✅ Real-time сообщения через WebSocket
- ✅ Сообщения хранятся в PostgreSQL (source of truth)
- ✅ Ответы на сообщения (reply)
- ✅ Редактирование сообщений
- ✅ Удаление (у себя / у обоих)
- ✅ Реакции (❤️ 👍 😂 😮 😢 🔥 🎉)
- ✅ Закрепление сообщений
- ✅ Статусы: отправлено ✓ / доставлено ✓✓ / прочитано ✓✓
- ✅ Индикатор "печатает..."
- ✅ Online / Offline статус
- ✅ Поиск по истории

### Медиа и файлы
- ✅ Загрузка фотографий (серверное хранение)
- ✅ Загрузка видео с streaming
- ✅ Загрузка файлов (PDF, DOC, ZIP и др.)
- ✅ Голосовые сообщения (iOS Safari совместимо)
- ✅ Камера (мобильные устройства)
- ✅ Полноэкранный просмотр изображений с zoom
- ✅ Скачивание файлов
- ✅ Автоматическое удаление старых файлов

### Безопасность
- ✅ Cookie-based auth (HttpOnly, Secure, SameSite)
- ✅ Session management с возможностью отзыва
- ✅ Безопасное хэширование паролей (bcrypt)
- ✅ Invite-система (максимум 2 пользователя)
- ✅ Файлы не публичны — проверка прав доступа
- ✅ Защита от path traversal
- ✅ MIME validation
- ✅ Streaming file uploads (не загружает в RAM)

### PWA и Push
- ✅ Progressive Web App
- ✅ Установка на домашний экран (iPhone/Android)
- ✅ Push-уведомления (Web Push + VAPID)
- ✅ Service Worker с кэшированием
- ✅ Standalone mode

### Интерфейс
- ✅ Dark / Light / System тема
- ✅ Responsive дизайн (mobile-first)
- ✅ Оптимизация под iPhone (Safe Area, Dynamic Island)
- ✅ Корректная работа с виртуальной клавиатурой

---

## 🚀 Быстрый старт (Development)

### Требования
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (или Docker)

### Автоматическая установка (Windows)

```bash
setup.bat
```

Этот скрипт:
- Проверит Python, Node.js, Docker
- Создаст `.env` файл
- Установит зависимости backend и frontend

### Запуск

```bash
start.bat
```

Откроет два окна:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

### Остановка

```bash
stop.bat
```

### Ручная установка

#### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Настроить .env
cp ../.env.example .env
# Отредактировать .env

# Запустить
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend
```bash
npm install
npm run dev
```

#### 3. Открыть
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

## 🌐 Деплой в Yandex Cloud

### Вариант 1: Serverless Containers + Managed PostgreSQL

#### 1. Создать Managed PostgreSQL
```bash
yc managed-postgresql cluster create \
  --name liana-db \
  --environment production \
  --network-name default \
  --host-name liana-db \
  --resource-preset s2.micro \
  --disk-size 10GB \
  --user-name liana \
  --user-password <пароль>
```

#### 2. Создать Object Storage для файлов
```bash
yc storage bucket create --name liana-files
```

#### 3. Создать Serverless Container
```bash
yc serverless container create \
  --name liana-backend \
  --memory 512MB \
  --execution-timeout 300s \
  --concurrency 10
```

#### 4. Деплой backend
```bash
yc serverless container revision deploy \
  --container-name liana-backend \
  --image cr.yandex/<registry-id>/liana-backend:latest \
  --environment \
    DATABASE_URL=postgresql://liana:<пароль>@liana-db:5432/liana,\
    SECRET_KEY=<секрет>,\
    FRONTEND_URL=https://chat.example.com
```

#### 5. Настроить домен и HTTPS
```bash
yc certificate-manager certificate create \
  --name liana-cert \
  --domain chat.example.com

yc serverless container create-binding \
  --container-name liana-backend \
  --domain chat.example.com
```

### Вариант 2: Compute VM (проще для начала)

#### 1. Создать VM
```bash
yc compute instance create \
  --name liana-server \
  --zone ru-central1-a \
  --network-interface subnet-name=default-1a,nat-ip-version=ipv4 \
  --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2204-lts \
  --memory 2 \
  --cores 2
```

#### 2. Подключиться и настроить
```bash
ssh user@<ip>

# Установить Docker
curl -fsSL https://get.docker.com | sh

# Клонировать проект
git clone <repo>
cd liana

# Настроить .env
cp .env.example .env
nano .env

# Запустить
docker compose up -d
```

#### 3. Настроить домен
- Направить A-запись `chat.example.com` на IP VM
- Получить SSL сертификат:
```bash
apt install certbot
certbot certonly --standalone -d chat.example.com
```

---

## 📱 Установка на iPhone

1. Открыть Safari → `https://chat.example.com`
2. Зарегистрироваться / Войти
3. Нажать кнопку «Поделиться» (⬆️)
4. Выбрать «На экран «Домой»»
5. Подтвердить

### Push-уведомления на iPhone
- Требуется iOS 16.4+
- После добавления на экран: Настройки → ПриватЧат → Уведомления → Разрешить

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
chmod +x scripts/backup.sh
./scripts/backup.sh

./scripts/restore.sh privatchat_backup_20240101_120000
```

### Windows
```powershell
.\scripts\backup.ps1
.\scripts\restore.ps1 -BackupName "privatchat_backup_20240101_120000"
```

---

## 🏗 Структура проекта

```
liana/
├── backend/
│   ├── app/
│   │   └── main.py          # FastAPI приложение
│   ├── alembic/
│   │   └── versions/        # Миграции БД
│   ├── tests/               # Тесты
│   ├── Dockerfile
│   └── requirements.txt
├── src/                     # Frontend (React)
│   ├── App.tsx
│   ├── components/
│   │   ├── AuthScreen.tsx
│   │   ├── ChatView.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── SettingsView.tsx
│   │   └── MediaViewer.tsx
│   ├── services/
│   │   ├── api.ts           # API клиент
│   │   ├── websocket.ts     # WebSocket сервис
│   │   └── push.ts          # Push уведомления
│   ├── stores/index.ts      # Zustand store
│   └── types/index.ts
├── public/
│   ├── manifest.json        # PWA manifest
│   ├── sw.js                # Service Worker
│   └── icon.svg
├── nginx/
│   └── nginx.conf
├── scripts/
│   ├── backup.sh
│   └── restore.sh
├── docker-compose.yml
├── .env.example
├── setup.bat                # Автоматическая установка (Windows)
├── start.bat                # Запуск (Windows)
├── stop.bat                 # Остановка (Windows)
└── README.md
```

---

## 🔧 Environment Variables

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `SECRET_KEY` | JWT secret (обязательно менять!) | — |
| `DB_PASSWORD` | Пароль PostgreSQL | — |
| `VAPID_PUBLIC_KEY` | VAPID public key для push | — |
| `VAPID_PRIVATE_KEY` | VAPID private key для push | — |
| `UPLOAD_DIR` | Директория для файлов | `./uploads` |
| `FILE_RETENTION_DAYS` | Хранение файлов (дни) | `30` |
| `MAX_FILE_SIZE_MB` | Макс. размер файла | `500` |
| `FRONTEND_URL` | URL фронтенда | `http://localhost:3000` |

---

## 🔒 Безопасность

### Реализовано
- ✅ HTTPS (обязательно для production)
- ✅ Secure cookies (HttpOnly, SameSite, Secure)
- ✅ CSRF protection
- ✅ XSS protection (React по умолчанию + CSP)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Rate limiting ready
- ✅ Безопасное хэширование паролей (bcrypt)
- ✅ Security headers
- ✅ Content Security Policy
- ✅ CORS
- ✅ WebSocket authentication (cookie-based)
- ✅ Проверка прав доступа к файлам
- ✅ Проверка размера файлов
- ✅ Проверка MIME типов
- ✅ Защита от path traversal
- ✅ Случайные имена файлов
- ✅ Запрет исполнения загруженных файлов

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
