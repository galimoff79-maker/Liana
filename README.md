# ПриватЧат — Private Messenger for Two

Production-ready private web messenger for two users. Full support for iPhone, Android, and Windows. PWA with push notifications.

---

## ✅ Implemented Features

### Core Messaging
- ✅ Real-time messaging via WebSocket
- ✅ Messages stored in PostgreSQL (source of truth)
- ✅ Reply to messages
- ✅ Edit messages
- ✅ Delete for me / Delete for all
- ✅ Reactions (❤️ 👍 😂 😮 😢 🔥 🎉)
- ✅ Pin messages
- ✅ Status: sent ✓ / delivered ✓✓ / read ✓✓
- ✅ Typing indicator
- ✅ Online / Offline status
- ✅ Search messages

### Media & Files
- ✅ Photo upload (server-side storage)
- ✅ Video upload with streaming
- ✅ File upload (PDF, DOC, ZIP, etc.)
- ✅ Voice messages (iOS Safari compatible)
- ✅ Camera capture (mobile)
- ✅ Full-screen image viewer with zoom
- ✅ File download
- ✅ Automatic file expiration (configurable)

### Authentication & Security
- ✅ Cookie-based authentication (HttpOnly, Secure, SameSite)
- ✅ Session management with revocation
- ✅ Password hashing (bcrypt)
- ✅ Invite system (max 2 users)
- ✅ Rate limiting ready
- ✅ File access control (not public)
- ✅ Path traversal protection
- ✅ MIME type validation
- ✅ Streaming file uploads (no RAM overload)

### PWA & Push
- ✅ Progressive Web App
- ✅ Install to home screen (iPhone/Android)
- ✅ Push notifications (Web Push + VAPID)
- ✅ Service Worker with caching
- ✅ Standalone mode
- ✅ iOS 16.4+ push support

### UI/UX
- ✅ Dark / Light / System theme
- ✅ Responsive design (mobile-first)
- ✅ iOS Safe Area support
- ✅ Virtual keyboard handling
- ✅ Modern messenger-style UI

### Infrastructure
- ✅ Docker + Docker Compose
- ✅ PostgreSQL (internal network)
- ✅ Nginx reverse proxy
- ✅ WebSocket support
- ✅ HTTPS ready (Let's Encrypt)
- ✅ Health checks
- ✅ Automatic file cleanup

---

## 🚀 Quick Start (Development)

### Requirements
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+

### 1. Clone
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

# Configure .env
cp ../.env.example .env
# Edit .env with your values

# Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend
```bash
npm install
npm run dev
```

### 4. Open
```
http://localhost:3000
```

---

## 🐳 Docker (Production)

### 1. Prepare
```bash
cp .env.example .env
```

Edit `.env`:
```env
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(64))">
DB_PASSWORD=<strong_password>
FRONTEND_URL=https://chat.example.com
```

### 2. Start
```bash
docker compose up -d
```

### 3. Check
```bash
docker compose ps
docker compose logs -f backend
```

---

## 🌐 Domain & HTTPS

### 1. DNS
Point A record `chat.example.com` to your VPS IP.

### 2. Let's Encrypt
```bash
apt install certbot
certbot certonly --standalone -d chat.example.com

# Copy certificates
cp /etc/letsencrypt/live/chat.example.com/fullchain.pem nginx/ssl/
cp /etc/letsencrypt/live/chat.example.com/privkey.pem nginx/ssl/
```

### 3. Restart
```bash
docker compose restart nginx
```

---

## 📱 iPhone Installation

1. Open Safari → `https://chat.example.com`
2. Register / Login
3. Tap Share button (⬆️)
4. Select "Add to Home Screen"
5. Confirm

### Push Notifications (iOS 16.4+)
- Must be added to home screen first
- Settings → ПриватЧат → Notifications → Allow

---

## 📱 Android Installation

1. Open Chrome → `https://chat.example.com`
2. Register / Login
3. Chrome will prompt "Add to home screen"
4. Or: menu (⋮) → "Install app"

---

## 💻 Windows

Open in browser:
```
https://chat.example.com
```

Supported: Chrome, Edge, Firefox.

Install as app:
- Chrome: address bar → install icon
- Edge: menu → Apps → Install this site as an app

---

## 🔔 Push Notifications

### Generate VAPID keys
```bash
npx web-push generate-vapid-keys
```

Add to `.env`:
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

## 🏗 Project Structure

```
privatchat/
├── backend/
│   ├── app/
│   │   └── main.py          # FastAPI application
│   ├── Dockerfile
│   └── requirements.txt
├── src/                      # Frontend (React)
│   ├── App.tsx
│   ├── components/
│   │   ├── AuthScreen.tsx
│   │   ├── ChatView.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── SettingsView.tsx
│   │   └── MediaViewer.tsx
│   ├── services/
│   │   ├── api.ts           # API client
│   │   ├── websocket.ts     # WebSocket service
│   │   └── push.ts          # Push notifications
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
└── README.md
```

---

## 🔧 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://...` |
| `SECRET_KEY` | JWT secret (REQUIRED, min 32 chars) | — |
| `DB_PASSWORD` | PostgreSQL password | — |
| `VAPID_PUBLIC_KEY` | VAPID public key for push | — |
| `VAPID_PRIVATE_KEY` | VAPID private key for push | — |
| `FILE_RETENTION_DAYS` | File storage duration | `30` |
| `MAX_FILE_SIZE_MB` | Max file size | `500` |
| `FRONTEND_URL` | Frontend URL | `http://localhost:3000` |

---

## 🔒 Security

### Implemented
- ✅ HTTPS (production)
- ✅ HttpOnly Secure SameSite cookies
- ✅ Password hashing (bcrypt)
- ✅ Session management with revocation
- ✅ File access control
- ✅ Path traversal protection
- ✅ MIME validation
- ✅ Streaming uploads
- ✅ WebSocket authentication
- ✅ CORS (minimal)
- ✅ Security headers (CSP, HSTS, X-Frame-Options)

### Recommendations
- Change `SECRET_KEY` before production
- Use strong PostgreSQL password
- Renew Let's Encrypt certificates
- Regular backups
- Update dependencies

---

## 📋 Browser Limitations

### iOS Safari
- Web Push only after adding PWA to home screen (iOS 16.4+)
- MediaRecorder support limited (iOS 14.3+)
- No background WebSocket (when minimized)
- File upload size limit (~500MB)

### Android Chrome
- Full feature support
- Push works without restrictions

### Desktop (Chrome/Edge/Firefox)
- Full feature support
- Push via Service Worker

---

## 🔮 Future Improvements (v2)

- End-to-End Encryption (E2EE)
- Voice calls (WebRTC)
- Video calls
- Group chats
- Multiple chats
- Sticker packs
- GIF search
- Disappearing messages
- Two-factor authentication
- Chat history export

---

## 📄 License

Private use only.
