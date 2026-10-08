# Liana — Приватный мессенджер для двоих

Приватный веб-мессенджер для общения двух людей через интернет. Работает на iPhone, Android и Windows.

---

## 🚀 Быстрый старт (3 шага)

### Шаг 1: Установите необходимые программы

Скачайте и установите (если ещё не установлены):

1. **Python** — https://www.python.org/downloads/
   - ⚠️ При установке ОБЯЗАТЕЛЬНО отметьте: **"Add Python to PATH"**

2. **Node.js** — https://nodejs.org/
   - Скачайте версию **LTS**

### Шаг 2: Запустите установку

Дважды кликните на файл:

```
setup.bat
```

Дождитесь окончания установки (2-5 минут).

### Шаг 3: Запустите Liana

Дважды кликните на файл:

```
start.bat
```

Откроется браузер с адресом: **http://localhost:3000**

---

## 📱 Как пользоваться

### Первый пользователь

1. Откройте http://localhost:3000
2. Нажмите **"Создать аккаунт"**
3. Заполните форму
4. Система покажет **код-приглашение** — скопируйте его

### Второй пользователь

1. Откройте http://localhost:3000 на другом устройстве
2. Нажмите **"Войти по коду-приглашению"**
3. Введите код от первого пользователя
4. Заполните форму

### Готово!

Теперь два человека могут общаться через Liana.

---

## 🛑 Остановка

Чтобы остановить Liana, дважды кликните:

```
stop.bat
```

---

## 📋 Файлы проекта

| Файл | Назначение |
|------|-----------|
| `setup.bat` | Установка (запустить один раз) |
| `start.bat` | Запуск Liana |
| `stop.bat` | Остановка Liana |
| `setup.ps1` | PowerShell версия установки |
| `start.ps1` | PowerShell версия запуска |
| `stop.ps1` | PowerShell версия остановки |

---

## 🔧 Если что-то не работает

### Python не найден

**Ошибка:** `Python не найден`

**Решение:**
1. Переустановите Python с https://www.python.org/downloads/
2. При установке отметьте **"Add Python to PATH"**
3. Перезагрузите компьютер
4. Запустите `setup.bat` снова

### Node.js не найден

**Ошибка:** `Node.js не найден`

**Решение:**
1. Скачайте Node.js с https://nodejs.org/
2. Установите версию LTS
3. Перезагрузите компьютер
4. Запустите `setup.bat` снова

### Backend не запускается

**Решение:**
1. Проверьте файл `backend.log`
2. Убедитесь что порт 8000 не занят
3. Перезапустите `stop.bat` затем `start.bat`

### Frontend не запускается

**Решение:**
1. Проверьте файл `frontend.log`
2. Убедитесь что порт 3000 не занят
3. Перезапустите `stop.bat` затем `start.bat`

---

## 🌐 Доступ из интернета (для iPhone)

Чтобы открыть Liana на iPhone из другой сети, нужно опубликовать её в интернете.

### Вариант 1: Yandex Cloud (рекомендуется)

Следуйте инструкции в разделе **Деплой в Yandex Cloud** ниже.

### Вариант 2: Ngrok (быстрый тест)

1. Скачайте ngrok: https://ngrok.com/download
2. Запустите:
   ```
   ngrok http 3000
   ```
3. Получите публичную ссылку вида: `https://xxxx.ngrok.io`
4. Откройте эту ссылку на iPhone

⚠️ **Внимание:** Ngrok подходит только для тестирования. Для постоянного использования нужен Yandex Cloud.

---

## 📱 Установка на iPhone

1. Откройте Safari
2. Перейдите по ссылке Liana (например: `https://chat.example.com`)
3. Зарегистрируйтесь / войдите
4. Нажмите кнопку **"Поделиться"** (⬆️)
5. Выберите **"На экран Домой"**
6. Подтвердите

Теперь Liana работает как приложение на iPhone.

---

## 🗄 Деплой в Yandex Cloud

### Что нужно

- Аккаунт Yandex Cloud
- Домен (например: `chat.example.com`)

### Пошаговая инструкция

#### 1. Создайте виртуальную машину

```bash
yc compute instance create \
  --name liana-server \
  --zone ru-central1-a \
  --network-interface subnet-name=default-1a,nat-ip-version=ipv4 \
  --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2204-lts \
  --memory 2 \
  --cores 2 \
  --platform-id standard-v3
```

#### 2. Подключитесь к серверу

```bash
ssh user@<IP-адрес-сервера>
```

#### 3. Установите Docker

```bash
curl -fsSL https://get.docker.com | sh
```

#### 4. Клонируйте проект

```bash
git clone <ваш-репозиторий>
cd liana
```

#### 5. Настройте окружение

```bash
cp .env.example .env
nano .env
```

Измените:
```env
SECRET_KEY=<сгенерируйте: python -c "import secrets; print(secrets.token_urlsafe(64))">
FRONTEND_URL=https://chat.example.com
```

#### 6. Запустите Docker

```bash
docker compose up -d
```

#### 7. Настройте домен

- Направьте A-запись `chat.example.com` на IP сервера
- Получите SSL сертификат:

```bash
apt install certbot
certbot certonly --standalone -d chat.example.com
```

- Скопируйте сертификаты:

```bash
mkdir -p nginx/ssl
cp /etc/letsencrypt/live/chat.example.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/chat.example.com/privkey.pem nginx/ssl/
```

- Перезапустите nginx:

```bash
docker compose restart nginx
```

#### 8. Готово!

Откройте `https://chat.example.com` на iPhone.

---

## 🔒 Безопасность

- ✅ HTTPS (обязательно для production)
- ✅ Безопасные cookies (HttpOnly, Secure, SameSite)
- ✅ Хэширование паролей (bcrypt)
- ✅ Защита от XSS, CSRF, SQL injection
- ✅ Файлы не публичны
- ✅ WebSocket authentication

---

## 📦 Структура проекта

```
liana/
├── backend/          # Python backend (FastAPI)
├── src/              # React frontend
├── public/           # PWA файлы
├── nginx/            # Nginx конфигурация
├── docker-compose.yml
├── setup.bat         # Установка
├── start.bat         # Запуск
├── stop.bat          # Остановка
└── README.md         # Эта инструкция
```

---

## 🆘 Поддержка

Если возникли проблемы:

1. Проверьте логи: `backend.log`, `frontend.log`, `setup.log`
2. Убедитесь что Python и Node.js установлены правильно
3. Попробуйте переустановить: `stop.bat` → `setup.bat` → `start.bat`

---

## 📄 Лицензия

Private use only.
