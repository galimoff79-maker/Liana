import { useState, useRef } from 'react';
import { format, parseISO } from 'date-fns';
import { Check, CheckCheck, Reply, Pencil, Trash2, Copy, Pin } from 'lucide-react';
import type { Message, User } from '../types';
import { useStore } from '../stores';
import { api } from '../services/api';

const REACTIONS = ['❤️', '👍', '😂', '😮', '😢', '🔥', '🎉'];

interface Props {
  message: Message;
  sender: User;
  isOwn: boolean;
  onReply: (msg: Message) => void;
  onEdit: (msg: Message) => void;
  onDelete: (msg: Message, forAll: boolean) => void;
  onMediaClick: (url: string, type: string) => void;
}

export default function MessageBubble({ message, sender, isOwn, onReply, onEdit, onDelete, onMediaClick }: Props) {
  const [showMenu, setShowMenu] = useState(false);
  const [showReactions, setShowReactions] = useState(false);
  const [menuPos, setMenuPos] = useState({ x: 0, y: 0 });
  const menuRef = useRef<HTMLDivElement>(null);
  const { currentUser, addReaction, removeReaction, messages, updateMessage } = useStore();

  if (message.deletedForAll) {
    return (
      <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'} px-4 py-0.5`}>
        <div className="px-3 py-2 rounded-xl text-sm italic" style={{ color: 'var(--text-muted)', background: 'var(--bg-tertiary)' }}>
          Message deleted
        </div>
      </div>
    );
  }

  const time = format(parseISO(message.timestamp), 'HH:mm');
  const isRead = message.readBy.length > 0 && !isOwn;
  const isDelivered = message.deliveredTo.length > 0 || isRead;

  const replyMsg = message.replyTo ? messages.find(m => m.id === message.replyTo) : null;

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    const x = Math.min(e.clientX, window.innerWidth - 200);
    const y = Math.min(e.clientY, window.innerHeight - 300);
    setMenuPos({ x, y });
    setShowMenu(true);
  };

  const handleLongPress = (e: React.TouchEvent) => {
    const timer = setTimeout(() => {
      const touch = e.touches[0];
      const x = Math.min(touch.clientX, window.innerWidth - 200);
      const y = Math.min(touch.clientY, window.innerHeight - 300);
      setMenuPos({ x, y });
      setShowMenu(true);
    }, 500);
    const clear = () => clearTimeout(timer);
    e.currentTarget.addEventListener('touchend', clear, { once: true });
    e.currentTarget.addEventListener('touchmove', clear, { once: true });
  };

  const handleReaction = async (emoji: string) => {
    try {
      const result = await api.toggleReaction(message.id, emoji);
      updateMessage(message.id, { reactions: result.reactions });
    } catch (error) {
      console.error('Failed to toggle reaction:', error);
    }
    setShowReactions(false);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    setShowMenu(false);
  };

  const renderAttachments = () => {
    return message.attachments.map(att => {
      if (att.expired) {
        return <div key={att.id} className="text-sm italic mt-1" style={{ color: 'var(--text-muted)' }}>File no longer available</div>;
      }
      if (att.type === 'image') {
        return (
          <div key={att.id} className="mt-1 cursor-pointer rounded-xl overflow-hidden max-w-[280px]" onClick={() => onMediaClick(att.url, 'image')}>
            <img src={att.url} alt={att.name} className="w-full h-auto max-h-[300px] object-cover" loading="lazy" />
          </div>
        );
      }
      if (att.type === 'video') {
        return (
          <div key={att.id} className="mt-1 rounded-xl overflow-hidden max-w-[280px]">
            <video src={att.url} controls className="w-full max-h-[300px]" preload="metadata" />
          </div>
        );
      }
      if (att.type === 'voice') {
        return (
          <div key={att.id} className="mt-1 flex items-center gap-2 px-2 py-1 rounded-lg" style={{ background: 'rgba(255,255,255,0.1)' }}>
            <audio src={att.url} controls className="h-8" style={{ maxWidth: '200px' }} />
            {att.duration && <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{Math.floor(att.duration / 60)}:{String(att.duration % 60).padStart(2, '0')}</span>}
          </div>
        );
      }
      return (
        <a key={att.id} href={att.url} download={att.name} className="mt-1 flex items-center gap-2 px-3 py-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.1)' }}>
          <span className="text-lg">📄</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm truncate">{att.name}</p>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{(att.size / 1024 / 1024).toFixed(1)} MB</p>
          </div>
        </a>
      );
    });
  };

  const myReactions = currentUser ? Object.entries(message.reactions).filter(([_, users]) => users.includes(currentUser.id)).map(([emoji]) => emoji) : [];

  return (
    <>
      <div
        className={`flex ${isOwn ? 'justify-end' : 'justify-start'} px-3 sm:px-4 py-0.5 group`}
        onContextMenu={handleContextMenu}
        onTouchStart={handleLongPress}
      >
        <div className={`max-w-[85%] sm:max-w-[70%] relative`}>
          {/* Reply preview */}
          {replyMsg && (
            <div className="mb-1 px-3 py-1.5 rounded-t-xl border-l-3 text-sm cursor-pointer" style={{ background: 'rgba(124,92,252,0.15)', borderLeftColor: 'var(--accent)' }}
              onClick={() => {
                const el = document.getElementById(`msg-${replyMsg.id}`);
                el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
              }}>
              <p className="font-medium text-xs" style={{ color: 'var(--accent)' }}>
                {replyMsg.senderId === currentUser?.id ? 'You' : sender.displayName}
              </p>
              <p className="truncate text-xs" style={{ color: 'var(--text-secondary)' }}>{replyMsg.text}</p>
            </div>
          )}

          <div
            id={`msg-${message.id}`}
            className={`px-3 py-2 ${isOwn ? 'msg-tail-out' : 'msg-tail-in'}`}
            style={{ background: isOwn ? 'var(--bg-message-out)' : 'var(--bg-message-in)' }}
          >
            {/* Text */}
            {message.text && (
              <p className="msg-text text-[15px] leading-relaxed whitespace-pre-wrap break-words" style={isOwn ? { color: 'white' } : {}}>
                {message.text}
              </p>
            )}

            {/* Attachments */}
            {renderAttachments()}

            {/* Footer */}
            <div className={`flex items-center gap-1 mt-0.5 ${isOwn ? 'justify-end' : 'justify-start'}`}>
              {message.edited && (
                <span className="text-[10px]" style={{ color: isOwn ? 'rgba(255,255,255,0.6)' : 'var(--text-muted)' }}>edited</span>
              )}
              <span className="text-[11px]" style={{ color: isOwn ? 'rgba(255,255,255,0.6)' : 'var(--text-muted)' }}>{time}</span>
              {isOwn && (
                <span style={{ color: isRead ? '#7c5cfc' : 'rgba(255,255,255,0.6)' }}>
                  {isRead ? <CheckCheck size={14} /> : isDelivered ? <CheckCheck size={14} /> : <Check size={14} />}
                </span>
              )}
            </div>
          </div>

          {/* Reactions */}
          {Object.keys(message.reactions).length > 0 && (
            <div className={`flex flex-wrap gap-1 mt-1 ${isOwn ? 'justify-end' : 'justify-start'}`}>
              {Object.entries(message.reactions).map(([emoji, users]) => (
                <button
                  key={emoji}
                  onClick={() => handleReaction(emoji)}
                  className="flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs border"
                  style={{
                    background: myReactions.includes(emoji) ? 'rgba(124,92,252,0.2)' : 'var(--bg-tertiary)',
                    borderColor: myReactions.includes(emoji) ? 'var(--accent)' : 'var(--border)'
                  }}
                >
                  <span>{emoji}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{users.length}</span>
                </button>
              ))}
            </div>
          )}

          {/* Quick reaction on hover */}
          <button
            className={`absolute ${isOwn ? '-left-8' : '-right-8'} top-1 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-full`}
            style={{ background: 'var(--bg-tertiary)' }}
            onClick={() => setShowReactions(!showReactions)}
          >
            <span className="text-sm">😊</span>
          </button>
        </div>
      </div>

      {/* Reaction picker */}
      {showReactions && (
        <div className="fixed inset-0 z-50" onClick={() => setShowReactions(false)}>
          <div className="fixed left-1/2 -translate-x-1/2 top-1/2 reaction-picker" onClick={e => e.stopPropagation()}>
            {REACTIONS.map(emoji => (
              <button key={emoji} className="reaction-btn" onClick={() => handleReaction(emoji)}>{emoji}</button>
            ))}
          </div>
        </div>
      )}

      {/* Context menu */}
      {showMenu && (
        <div className="fixed inset-0 z-50" onClick={() => setShowMenu(false)}>
          <div ref={menuRef} className="context-menu" style={{ left: menuPos.x, top: menuPos.y }} onClick={e => e.stopPropagation()}>
            <div className="context-menu-item" onClick={() => { onReply(message); setShowMenu(false); }}>
              <Reply size={16} /> Reply
            </div>
            <div className="context-menu-item" onClick={handleCopy}>
              <Copy size={16} /> Copy
            </div>
            {isOwn && message.text && (
              <div className="context-menu-item" onClick={() => { onEdit(message); setShowMenu(false); }}>
                <Pencil size={16} /> Edit
              </div>
            )}
            <div className="context-menu-item" onClick={() => { updateMessage(message.id, { pinned: !message.pinned }); setShowMenu(false); }}>
              <Pin size={16} /> {message.pinned ? 'Unpin' : 'Pin'}
            </div>
            {isOwn && (
              <>
                <div className="context-menu-item danger" onClick={() => { onDelete(message, false); setShowMenu(false); }}>
                  <Trash2 size={16} /> Delete for me
                </div>
                <div className="context-menu-item danger" onClick={() => { onDelete(message, true); setShowMenu(false); }}>
                  <Trash2 size={16} /> Delete for all
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
