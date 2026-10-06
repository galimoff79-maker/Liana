"""
ПриватЧат Backend - FastAPI Application
Приватный мессенджер для двоих пользователей
"""
import os
import uuid
import hashlib
import secrets
import mimetypes
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, Text, Boolean, DateTime, Integer, ForeignKey, JSON, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from jose import jwt, JWTError
from passlib.context import CryptContext

# ============ Configuration ============
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://privatchat:privatchat@localhost:5432/privatchat")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
FILE_RETENTION_DAYS = int(os.getenv("FILE_RETENTION_DAYS", "30"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
MAX_USERS = 2

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============ Database ============
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============ Models ============
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_path = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Session_(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    device_info = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    text = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    deleted = Column(Boolean, default=False)
    deleted_for_all = Column(Boolean, default=False)
    reply_to = Column(String, ForeignKey("messages.id"), nullable=True)
    reactions = Column(JSON, default=dict)
    pinned = Column(Boolean, default=False)
    voice_duration = Column(Integer, nullable=True)
    read_by = Column(JSON, default=list)
    delivered_to = Column(JSON, default=list)

class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    type = Column(String(20), nullable=False)  # image, video, voice, file
    name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    thumbnail_path = Column(String(1000), nullable=True)
    size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    duration = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class Invite(Base):
    __tablename__ = "invites"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), unique=True, nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    used = Column(Boolean, default=False)
    used_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(String(500), nullable=False)
    auth = Column(String(500), nullable=False)
    device_info = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# ============ Security ============
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)

def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire, "jti": str(uuid.uuid4())}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

# ============ Dependencies ============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def check_user_limit(db: Session):
    count = db.query(User).count()
    if count >= MAX_USERS:
        raise HTTPException(status_code=403, detail="Регистрация закрыта. Максимум 2 пользователя.")

# ============ Pydantic Schemas ============
class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str

class LoginRequest(BaseModel):
    username: str
    password: str

class InviteRegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str
    invite_code: str

class MessageSendRequest(BaseModel):
    text: str = ""
    reply_to: Optional[str] = None

class MessageEditRequest(BaseModel):
    text: str

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    username: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class PushSubscriptionRequest(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    device_info: Optional[str] = None

# ============ FastAPI App ============
app = FastAPI(title="ПриватЧат API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ WebSocket Manager ============
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except:
                    pass

    async def broadcast(self, message: dict, exclude_user: str = None):
        for user_id, connections in self.active_connections.items():
            if user_id != exclude_user:
                for ws in connections:
                    try:
                        await ws.send_json(message)
                    except:
                        pass

manager = ConnectionManager()

# ============ Auth Routes ============
@app.post("/api/auth/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    check_user_limit(db)
    
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Имя пользователя минимум 3 символа")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Пароль минимум 6 символов")
    
    user = User(
        username=req.username,
        display_name=req.display_name,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create invite code for second user
    invite_code = secrets.token_urlsafe(8).upper()[:8]
    invite = Invite(
        code=invite_code,
        created_by=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invite)
    db.commit()
    
    token = create_access_token(user.id)
    return {
        "token": token,
        "user": {"id": user.id, "username": user.username, "displayName": user.display_name},
        "invite_code": invite_code,
    }

@app.post("/api/auth/register-with-invite")
async def register_with_invite(req: InviteRegisterRequest, db: Session = Depends(get_db)):
    check_user_limit(db)
    
    invite = db.query(Invite).filter(
        Invite.code == req.invite_code.upper(),
        Invite.used == False,
    ).first()
    
    if not invite:
        raise HTTPException(status_code=400, detail="Неверный или использованный код-приглашение")
    
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Код-приглашение истёк")
    
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    user = User(
        username=req.username,
        display_name=req.display_name,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    invite.used = True
    invite.used_by = user.id
    db.commit()
    
    token = create_access_token(user.id)
    return {
        "token": token,
        "user": {"id": user.id, "username": user.username, "displayName": user.display_name},
    }

@app.post("/api/auth/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверные учётные данные")
    
    token = create_access_token(user.id)
    return {
        "token": token,
        "user": {"id": user.id, "username": user.username, "displayName": user.display_name},
    }

@app.post("/api/auth/logout")
async def logout(user: User = Depends(get_current_user)):
    return {"status": "ok"}

@app.post("/api/auth/change-password")
async def change_password(req: PasswordChangeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"status": "ok"}

# ============ User Routes ============
@app.get("/api/users/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "displayName": user.display_name,
        "bio": user.bio,
        "avatar": user.avatar_path,
        "online": user.online,
        "lastSeen": user.last_seen.isoformat() if user.last_seen else None,
    }

@app.get("/api/users/partner")
async def get_partner(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    partner = db.query(User).filter(User.id != user.id).first()
    if not partner:
        return None
    return {
        "id": partner.id,
        "username": partner.username,
        "displayName": partner.display_name,
        "bio": partner.bio,
        "avatar": partner.avatar_path,
        "online": partner.online,
        "lastSeen": partner.last_seen.isoformat() if partner.last_seen else None,
    }

@app.put("/api/users/me")
async def update_profile(req: ProfileUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.bio is not None:
        user.bio = req.bio
    if req.username is not None and req.username != user.username:
        if db.query(User).filter(User.username == req.username).first():
            raise HTTPException(status_code=400, detail="Username занят")
        user.username = req.username
    db.commit()
    return {"status": "ok"}

@app.post("/api/users/me/avatar")
async def upload_avatar(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ext = Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / "avatars" / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB limit for avatars
        raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 5MB)")
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    user.avatar_path = f"/api/files/avatars/{filename}"
    db.commit()
    return {"url": user.avatar_path}

# ============ Message Routes ============
@app.get("/api/messages")
async def get_messages(
    limit: int = 50,
    before: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Message).filter(Message.deleted_for_all == False).order_by(Message.timestamp.desc())
    if before:
        msg = db.query(Message).filter(Message.id == before).first()
        if msg:
            query = query.filter(Message.timestamp < msg.timestamp)
    messages = query.limit(limit).all()
    messages.reverse()
    
    result = []
    for msg in messages:
        attachments = db.query(Attachment).filter(Attachment.message_id == msg.id).all()
        result.append({
            "id": msg.id,
            "senderId": msg.sender_id,
            "text": msg.text if not msg.deleted else "",
            "timestamp": msg.timestamp.isoformat(),
            "edited": msg.edited,
            "editedAt": msg.edited_at.isoformat() if msg.edited_at else None,
            "deleted": msg.deleted,
            "deletedForAll": msg.deleted_for_all,
            "replyTo": msg.reply_to,
            "reactions": msg.reactions or {},
            "pinned": msg.pinned,
            "readBy": msg.read_by or [],
            "deliveredTo": msg.delivered_to or [],
            "attachments": [{
                "id": a.id,
                "type": a.type,
                "name": a.name,
                "url": f"/api/files/{a.file_path}",
                "size": a.size,
                "mimeType": a.mime_type,
                "duration": a.duration,
                "expired": a.expires_at and a.expires_at < datetime.utcnow(),
            } for a in attachments],
        })
    return result

@app.post("/api/messages")
async def send_message(
    req: MessageSendRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = Message(
        sender_id=user.id,
        text=req.text,
        reply_to=req.reply_to,
        delivered_to=[user.id],
        read_by=[],
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    # Notify partner via WebSocket
    partner = db.query(User).filter(User.id != user.id).first()
    if partner:
        await manager.send_to_user(partner.id, {
            "type": "new_message",
            "message": {
                "id": msg.id,
                "senderId": msg.sender_id,
                "text": msg.text,
                "timestamp": msg.timestamp.isoformat(),
                "replyTo": msg.reply_to,
            }
        })
    
    return {"id": msg.id, "timestamp": msg.timestamp.isoformat()}

@app.put("/api/messages/{message_id}")
async def edit_message(
    message_id: str,
    req: MessageEditRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    if msg.sender_id != user.id:
        raise HTTPException(status_code=403, detail="Нет прав")
    
    msg.text = req.text
    msg.edited = True
    msg.edited_at = datetime.utcnow()
    db.commit()
    
    partner = db.query(User).filter(User.id != user.id).first()
    if partner:
        await manager.send_to_user(partner.id, {
            "type": "message_edited",
            "messageId": msg.id,
            "text": msg.text,
            "editedAt": msg.edited_at.isoformat(),
        })
    
    return {"status": "ok"}

@app.delete("/api/messages/{message_id}")
async def delete_message(
    message_id: str,
    for_all: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    if msg.sender_id != user.id:
        raise HTTPException(status_code=403, detail="Нет прав")
    
    if for_all:
        msg.deleted = True
        msg.deleted_for_all = True
        msg.text = ""
    else:
        # Delete only for current user (soft delete - mark in read_by)
        pass
    
    db.commit()
    
    partner = db.query(User).filter(User.id != user.id).first()
    if partner and for_all:
        await manager.send_to_user(partner.id, {
            "type": "message_deleted",
            "messageId": msg.id,
        })
    
    return {"status": "ok"}

@app.post("/api/messages/{message_id}/reactions")
async def toggle_reaction(
    message_id: str,
    emoji: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    
    reactions = msg.reactions or {}
    if emoji not in reactions:
        reactions[emoji] = []
    
    if user.id in reactions[emoji]:
        reactions[emoji] = [uid for uid in reactions[emoji] if uid != user.id]
        if not reactions[emoji]:
            del reactions[emoji]
    else:
        reactions[emoji].append(user.id)
    
    msg.reactions = reactions
    db.commit()
    
    partner = db.query(User).filter(User.id != user.id).first()
    if partner:
        await manager.send_to_user(partner.id, {
            "type": "reaction_updated",
            "messageId": msg.id,
            "reactions": reactions,
        })
    
    return {"reactions": reactions}

@app.post("/api/messages/{message_id}/read")
async def mark_read(
    message_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404)
    
    read_by = msg.read_by or []
    if user.id not in read_by:
        read_by.append(user.id)
        msg.read_by = read_by
        db.commit()
    
    partner = db.query(User).filter(User.id != user.id).first()
    if partner:
        await manager.send_to_user(partner.id, {
            "type": "message_read",
            "messageId": msg.id,
            "userId": user.id,
        })
    
    return {"status": "ok"}

# ============ File Upload ============
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    message_id: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = await file.read()
    max_size = MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail=f"Файл слишком большой (макс. {MAX_FILE_SIZE_MB}MB)")
    
    # Determine type
    mime = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    if mime.startswith("image/"):
        file_type = "image"
    elif mime.startswith("video/"):
        file_type = "video"
    elif mime.startswith("audio/"):
        file_type = "voice"
    else:
        file_type = "file"
    
    # Save with random name
    ext = Path(file.filename).suffix.lower()
    filename = f"{uuid.uuid4()}{ext}"
    subdir = file_type + "s"
    filepath = UPLOAD_DIR / subdir / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    expires_at = datetime.utcnow() + timedelta(days=FILE_RETENTION_DAYS)
    
    # Create or update message
    if message_id:
        msg = db.query(Message).filter(Message.id == message_id).first()
    else:
        msg = Message(sender_id=user.id, text="", delivered_to=[user.id], read_by=[])
        db.add(msg)
        db.flush()
    
    attachment = Attachment(
        message_id=msg.id,
        type=file_type,
        name=file.filename,
        file_path=f"{subdir}/{filename}",
        size=len(content),
        mime_type=mime,
        expires_at=expires_at,
    )
    db.add(attachment)
    db.commit()
    
    return {
        "messageId": msg.id,
        "attachment": {
            "id": attachment.id,
            "type": file_type,
            "name": file.filename,
            "url": f"/api/files/{subdir}/{filename}",
            "size": len(content),
            "mimeType": mime,
        }
    }

@app.get("/api/files/{path:path}")
async def get_file(path: str, user: User = Depends(get_current_user)):
    # Security: prevent path traversal
    safe_path = Path(path).name
    subdir = Path(path).parent.name
    
    # Check if avatars are public
    if subdir == "avatars":
        filepath = UPLOAD_DIR / "avatars" / safe_path
    else:
        filepath = UPLOAD_DIR / subdir / safe_path
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Verify user has access (check message ownership)
    # For simplicity, both users can access all files in their chat
    
    return FileResponse(filepath)

# ============ Search ============
@app.get("/api/search")
async def search_messages(
    q: str,
    type: Optional[str] = None,  # all, images, videos, files, voice
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Message).filter(
        Message.deleted_for_all == False,
        Message.text.ilike(f"%{q}%")
    ).order_by(Message.timestamp.desc()).limit(50)
    
    messages = query.all()
    return [{
        "id": m.id,
        "text": m.text,
        "senderId": m.sender_id,
        "timestamp": m.timestamp.isoformat(),
    } for m in messages]

# ============ WebSocket ============
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return
    
    await manager.connect(user_id, websocket)
    
    # Update online status
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.online = True
        user.last_seen = datetime.utcnow()
        db.commit()
        
        # Notify partner
        partner = db.query(User).filter(User.id != user_id).first()
        if partner:
            await manager.send_to_user(partner.id, {
                "type": "user_online",
                "userId": user_id,
            })
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "typing":
                partner = db.query(User).filter(User.id != user_id).first()
                if partner:
                    await manager.send_to_user(partner.id, {
                        "type": "typing",
                        "userId": user_id,
                        "isTyping": data.get("isTyping", True),
                    })
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.online = False
            user.last_seen = datetime.utcnow()
            db.commit()
            partner = db.query(User).filter(User.id != user_id).first()
            if partner:
                await manager.send_to_user(partner.id, {
                    "type": "user_offline",
                    "userId": user_id,
                    "lastSeen": datetime.utcnow().isoformat(),
                })
        db.close()

# ============ Push Notifications ============
@app.post("/api/push/subscribe")
async def subscribe_push(
    req: PushSubscriptionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sub = PushSubscription(
        user_id=user.id,
        endpoint=req.endpoint,
        p256dh=req.p256dh,
        auth=req.auth,
        device_info=req.device_info,
    )
    db.add(sub)
    db.commit()
    return {"status": "ok"}

# ============ File Cleanup Job ============
async def cleanup_expired_files():
    """Remove expired files from storage"""
    db = SessionLocal()
    try:
        expired = db.query(Attachment).filter(
            Attachment.expires_at < datetime.utcnow()
        ).all()
        for att in expired:
            filepath = UPLOAD_DIR / att.file_path
            if filepath.exists():
                filepath.unlink()
            if att.thumbnail_path:
                thumb = UPLOAD_DIR / att.thumbnail_path
                if thumb.exists():
                    thumb.unlink()
            db.delete(att)
        db.commit()
    finally:
        db.close()

@app.on_event("startup")
async def startup():
    # Start cleanup task
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    while True:
        await asyncio.sleep(3600)  # Every hour
        try:
            await cleanup_expired_files()
        except Exception as e:
            print(f"Cleanup error: {e}")

# ============ Health Check ============
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
