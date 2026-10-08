"""
ПриватЧат Backend - Production Ready
Real-time messenger for two users
"""
import os
import uuid
import hashlib
import secrets
import mimetypes
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Text, Boolean, DateTime, Integer, ForeignKey, JSON, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from jose import jwt, JWTError
from passlib.context import CryptContext
import aiofiles

# ============ Logging ============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ Configuration ============
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://privatchat:privatchat@localhost:5432/privatchat")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-min-32-chars!!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
FILE_RETENTION_DAYS = int(os.getenv("FILE_RETENTION_DAYS", "30"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
MAX_USERS = 2
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============ Database ============
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10)
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
    created_at = Column(DateTime, default=datetime.utcnow)

class Session_(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    device_info = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Boolean, default=False)

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    deleted_for_all = Column(Boolean, default=False, index=True)
    reply_to = Column(String, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    reactions = Column(JSON, default=dict)
    pinned = Column(Boolean, default=False)
    voice_duration = Column(Integer, nullable=True)
    read_by = Column(JSON, default=list)
    delivered_to = Column(JSON, default=list)

class MessageDeletion(Base):
    """Track messages deleted for specific users"""
    __tablename__ = "message_deletions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    deleted_at = Column(DateTime, default=datetime.utcnow)

class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    thumbnail_path = Column(String(1000), nullable=True)
    size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    duration = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)

class Invite(Base):
    __tablename__ = "invites"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), unique=True, nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    used = Column(Boolean, default=False)
    used_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(String(500), nullable=False)
    auth = Column(String(500), nullable=False)
    device_info = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ============ Security ============
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)

def create_access_token(user_id: str, jti: str) -> str:
    """Create JWT token with provided JTI (must match session.jti)"""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "jti": jti,
        "exp": expire
    }
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

def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = None
    
    # Try cookie first
    token = request.cookies.get("access_token")
    
    # Fallback to Authorization header
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        if not user_id or not jti:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if session is revoked
        session = db.query(Session_).filter(Session_.jti == jti, Session_.revoked == False).first()
        if not session:
            raise HTTPException(status_code=401, detail="Session revoked")
        
        # Update last active
        session.last_active = datetime.utcnow()
        db.commit()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def check_user_limit(db: Session):
    """Check if we can register another user (max 2)"""
    count = db.query(User).count()
    if count >= MAX_USERS:
        raise HTTPException(status_code=403, detail="Registration closed. Maximum 2 users.")

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

class ReadMessagesRequest(BaseModel):
    message_ids: List[str]

# ============ WebSocket Manager ============
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected")

    def is_user_online(self, user_id: str) -> bool:
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")

    async def broadcast_except(self, message: dict, exclude_user: str = None):
        for user_id, connections in self.active_connections.items():
            if user_id != exclude_user:
                for ws in connections:
                    try:
                        await ws.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {e}")

manager = ConnectionManager()

# ============ FastAPI App ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting ПриватЧат backend...")
    asyncio.create_task(periodic_cleanup())
    yield
    # Shutdown
    logger.info("Shutting down ПриватЧат backend...")

app = FastAPI(title="ПриватЧат API", version="2.0.0", lifespan=lifespan)

# Minimal CORS - only for development
if os.getenv("ENVIRONMENT") != "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ============ Auth Routes ============
@app.post("/api/auth/register")
async def register(req: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    check_user_limit(db)
    
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    user = User(
        username=req.username,
        display_name=req.display_name,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.flush()
    
    # Create session with JTI
    jti = str(uuid.uuid4())
    session = Session_(user_id=user.id, jti=jti, device_info="registration")
    db.add(session)
    
    # Create invite code
    invite_code = secrets.token_urlsafe(8).upper()[:8]
    invite = Invite(
        code=invite_code,
        created_by=user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invite)
    db.commit()
    
    token = create_access_token(user.id, jti)
    
    # Set HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {
        "token": token,
        "user": {"id": user.id, "username": user.username, "displayName": user.display_name},
        "invite_code": invite_code,
    }

@app.post("/api/auth/register-with-invite")
async def register_with_invite(req: InviteRegisterRequest, response: Response, db: Session = Depends(get_db)):
    check_user_limit(db)
    
    invite = db.query(Invite).filter(
        Invite.code == req.invite_code.upper(),
        Invite.used == False,
    ).first()
    
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or used invite code")
    
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite code expired")
    
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(
        username=req.username,
        display_name=req.display_name,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.flush()
    
    # Create session with JTI
    jti = str(uuid.uuid4())
    session = Session_(user_id=user.id, jti=jti, device_info="registration")
    db.add(session)
    
    invite.used = True
    invite.used_by = user.id
    db.commit()
    
    token = create_access_token(user.id, jti)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {
        "token": token,
        "user": {"id": user.id, "username": user.username, "displayName": user.display_name},
    }

@app.post("/api/auth/login")
async def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session with JTI
    jti = str(uuid.uuid4())
    session = Session_(user_id=user.id, jti=jti, device_info="login")
    db.add(session)
    db.commit()
    
    token = create_access_token(user.id, jti)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {
        "token": token,
        "user": {"id": user.id, "username": user.username, "displayName": user.display_name},
    }

@app.post("/api/auth/logout")
async def logout(request: Request, response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Revoke current session
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            if jti:
                session = db.query(Session_).filter(Session_.jti == jti).first()
                if session:
                    session.revoked = True
                    db.commit()
        except:
            pass
    
    response.delete_cookie("access_token")
    return {"status": "ok"}

@app.post("/api/auth/logout-all")
async def logout_all(response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Revoke all sessions for this user
    sessions = db.query(Session_).filter(Session_.user_id == user.id).all()
    for session in sessions:
        session.revoked = True
    db.commit()
    
    response.delete_cookie("access_token")
    return {"status": "ok"}

@app.post("/api/auth/change-password")
async def change_password(req: PasswordChangeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid current password")
    
    user.password_hash = hash_password(req.new_password)
    
    # Revoke all other sessions
    sessions = db.query(Session_).filter(Session_.user_id == user.id).all()
    for session in sessions:
        session.revoked = True
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
        "online": manager.is_user_online(user.id),
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
        "online": manager.is_user_online(partner.id),
    }

@app.put("/api/users/me")
async def update_profile(req: ProfileUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.bio is not None:
        user.bio = req.bio
    if req.username is not None and req.username != user.username:
        if db.query(User).filter(User.username == req.username).first():
            raise HTTPException(status_code=400, detail="Username taken")
        user.username = req.username
    db.commit()
    return {"status": "ok"}

@app.post("/api/users/me/avatar")
async def upload_avatar(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Validate MIME
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / "avatars" / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Stream file to disk
    size = 0
    async with aiofiles.open(filepath, 'wb') as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            size += len(chunk)
            if size > 5 * 1024 * 1024:  # 5MB limit
                filepath.unlink()
                raise HTTPException(status_code=400, detail="File too large (max 5MB)")
            await f.write(chunk)
    
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
    # Get messages not deleted for this user
    query = db.query(Message).filter(
        Message.deleted_for_all == False,
        ~Message.id.in_(
            db.query(MessageDeletion.message_id).filter(MessageDeletion.user_id == user.id)
        )
    ).order_by(Message.timestamp.desc())
    
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
            "text": msg.text if not msg.deleted_for_all else "",
            "timestamp": msg.timestamp.isoformat(),
            "edited": msg.edited,
            "editedAt": msg.edited_at.isoformat() if msg.edited_at else None,
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
    # Validate reply_to if provided
    if req.reply_to:
        reply_msg = db.query(Message).filter(Message.id == req.reply_to).first()
        if not reply_msg:
            raise HTTPException(status_code=400, detail="Reply message not found")
    
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
        
        # Send push notification if partner is offline
        if not manager.is_user_online(partner.id):
            await send_push_notification(partner.id, "Новое сообщение", req.text[:100], db)
    
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
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
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
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if for_all:
        msg.deleted_for_all = True
        msg.text = ""
    else:
        # Delete only for current user
        deletion = MessageDeletion(message_id=msg.id, user_id=user.id)
        db.add(deletion)
    
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
        raise HTTPException(status_code=404, detail="Message not found")
    
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

@app.post("/api/messages/read")
async def mark_messages_read(
    req: ReadMessagesRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for msg_id in req.message_ids:
        msg = db.query(Message).filter(Message.id == msg_id).first()
        if msg and msg.sender_id != user.id:
            read_by = msg.read_by or []
            if user.id not in read_by:
                read_by.append(user.id)
                msg.read_by = read_by
                
                # Notify sender
                sender = db.query(User).filter(User.id == msg.sender_id).first()
                if sender:
                    await manager.send_to_user(sender.id, {
                        "type": "message_read",
                        "messageId": msg.id,
                        "userId": user.id,
                    })
    
    db.commit()
    return {"status": "ok"}

# ============ File Upload ============
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    message_id: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Determine type from MIME
    mime = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    
    # Security: block executable files
    blocked_mimes = ['application/x-executable', 'application/x-msdownload', 'application/x-msi']
    if mime in blocked_mimes:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
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
    
    # Stream file to disk
    size = 0
    max_size = MAX_FILE_SIZE_MB * 1024 * 1024
    async with aiofiles.open(filepath, 'wb') as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            size += len(chunk)
            if size > max_size:
                filepath.unlink()
                raise HTTPException(status_code=400, detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)")
            await f.write(chunk)
    
    expires_at = datetime.utcnow() + timedelta(days=FILE_RETENTION_DAYS)
    
    # Create or use existing message
    if message_id:
        msg = db.query(Message).filter(Message.id == message_id).first()
        if not msg:
            filepath.unlink()
            raise HTTPException(status_code=404, detail="Message not found")
    else:
        msg = Message(sender_id=user.id, text="", delivered_to=[user.id], read_by=[])
        db.add(msg)
        db.flush()
    
    attachment = Attachment(
        message_id=msg.id,
        type=file_type,
        name=file.filename,
        file_path=f"{subdir}/{filename}",
        size=size,
        mime_type=mime,
        expires_at=expires_at,
    )
    db.add(attachment)
    db.commit()
    
    # Notify partner
    partner = db.query(User).filter(User.id != user.id).first()
    if partner:
        await manager.send_to_user(partner.id, {
            "type": "new_message",
            "message": {
                "id": msg.id,
                "senderId": msg.sender_id,
                "text": msg.text,
                "timestamp": msg.timestamp.isoformat(),
            }
        })
    
    return {
        "messageId": msg.id,
        "attachment": {
            "id": attachment.id,
            "type": file_type,
            "name": file.filename,
            "url": f"/api/files/{subdir}/{filename}",
            "size": size,
            "mimeType": mime,
        }
    }

@app.get("/api/files/{path:path}")
async def get_file(path: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Security: prevent path traversal
    if '..' in path or path.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # Check if avatar (public for authenticated users)
    if path.startswith("avatars/"):
        filepath = UPLOAD_DIR / path
    else:
        # Check attachment exists and user has access
        attachment = db.query(Attachment).filter(Attachment.file_path == path).first()
        if not attachment:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check expiration
        if attachment.expires_at and attachment.expires_at < datetime.utcnow():
            raise HTTPException(status_code=410, detail="File expired")
        
        # Check message exists
        message = db.query(Message).filter(Message.id == attachment.message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        filepath = UPLOAD_DIR / path
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(filepath)

# ============ Search ============
@app.get("/api/search")
async def search_messages(
    q: str,
    type: Optional[str] = None,
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
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    # Authenticate via cookie
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=4001)
        return
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        
        if not user_id or not jti:
            await websocket.close(code=4001)
            return
        
        # Check session
        session = db.query(Session_).filter(Session_.jti == jti, Session_.revoked == False).first()
        if not session:
            await websocket.close(code=4001)
            return
        
    except JWTError:
        await websocket.close(code=4001)
        return
    
    await manager.connect(user_id, websocket)
    
    # Notify partner
    partner = db.query(User).filter(User.id != user_id).first()
    if partner and manager.is_user_online(partner.id):
        await manager.send_to_user(partner.id, {
            "type": "user_online",
            "userId": user_id,
        })
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "typing":
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
        
        # Notify partner if user is fully offline
        if not manager.is_user_online(user_id) and partner:
            await manager.send_to_user(partner.id, {
                "type": "user_offline",
                "userId": user_id,
            })

# ============ Push Notifications ============
async def send_push_notification(user_id: str, title: str, body: str, db: Session):
    """Send push notification to user's devices"""
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        return
    
    try:
        from pywebpush import webpush, WebPushException
        
        subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
        
        for sub in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {
                            "p256dh": sub.p256dh,
                            "auth": sub.auth
                        }
                    },
                    data=f'{{"title":"{title}","body":"{body}"}}',
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": f"mailto:admin@{FRONTEND_URL}"}
                )
            except WebPushException as e:
                logger.error(f"Push failed for subscription {sub.id}: {e}")
                # Remove invalid subscription
                if e.response and e.response.status_code in [404, 410]:
                    db.delete(sub)
                    db.commit()
    except ImportError:
        logger.warning("pywebpush not installed, push notifications disabled")
    except Exception as e:
        logger.error(f"Push notification error: {e}")

@app.post("/api/push/subscribe")
async def subscribe_push(
    req: PushSubscriptionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if subscription already exists
    existing = db.query(PushSubscription).filter(
        PushSubscription.user_id == user.id,
        PushSubscription.endpoint == req.endpoint
    ).first()
    
    if existing:
        return {"status": "ok"}
    
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
        logger.info(f"Cleaned up {len(expired)} expired files")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
    finally:
        db.close()

async def periodic_cleanup():
    while True:
        await asyncio.sleep(3600)  # Every hour
        try:
            await cleanup_expired_files()
        except Exception as e:
            logger.error(f"Periodic cleanup error: {e}")

# ============ Health Check ============
@app.get("/api/health")
async def health(db: Session = Depends(get_db)):
    try:
        # Check database connection (SQLAlchemy 2.x requires text())
        db.execute(text("SELECT 1"))
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
