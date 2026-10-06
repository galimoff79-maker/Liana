import { useState, useRef, useEffect, useCallback } from 'react';
import { format, isToday, isYesterday, parseISO, isSameDay } from 'date-fns';
import { ru } from 'date-fns/locale';
import { Send, Paperclip, Mic, Smile, X, ArrowDown, Search, Settings, Phone, Video, MoreVertical, Camera, Pin } from 'lucide-react';
import { useStore } from '../stores';
import MessageBubble from './MessageBubble';
import type { Message, Attachment } from '../types';
import EmojiPicker from 'emoji-picker-react';

export default function ChatView() {
  const {
    currentUser, partner, messages, replyingTo, editingMessage,
    typingPartner, connectionStatus, showEmojiPicker,
    setReplyingTo, setEditingMessage, setShowEmojiPicker,
    addMessage, updateMessage, deleteMessage, markAsRead,
    setActiveView, setMediaViewer
  } = useStore();

  const [text, setText] = useState('');
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<number | null>(null);

  // Auto scroll
  const scrollToBottom = useCallback((smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
  }, []);

  useEffect(() => { scrollToBottom(false); }, []);

  // Handle visual viewport (keyboard) on mobile
  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;
    const handler = () => {
      // When keyboard opens, scroll to bottom
      if (document.activeElement?.tagName === 'TEXTAREA' || document.activeElement?.tagName === 'INPUT') {
        setTimeout(() => scrollToBottom(), 100);
      }
    };
    vv.addEventListener('resize', handler);
    return () => vv.removeEventListener('resize', handler);
  }, [scrollToBottom]);

  // Mark messages as read when visible
  useEffect(() => {
    const unread = messages.filter(m => m.senderId !== currentUser?.id && !m.readBy.includes(currentUser?.id || ''));
    if (unread.length > 0) {
      markAsRead(unread.map(m => m.id));
    }
  }, [messages, currentUser]);

  // Scroll detection
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = container;
      setShowScrollBtn(scrollHeight - scrollTop - clientHeight > 200);
    };
    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  // Send message
  const sendMessage = () => {
    if (!text.trim() && !editingMessage) return;

    if (editingMessage) {
      updateMessage(editingMessage.id, { text: text.trim(), edited: true, editedAt: new Date().toISOString() });
      setEditingMessage(null);
    } else {
      const msg: Message = {
        id: crypto.randomUUID(),
        chatId: 'main',
        senderId: currentUser!.id,
        text: text.trim(),
        timestamp: new Date().toISOString(),
        edited: false,
        deleted: false,
        deletedForAll: false,
        reactions: {},
        attachments: [],
        readBy: [],
        deliveredTo: [currentUser!.id],
        pinned: false,
        replyTo: replyingTo?.id,
      };
      addMessage(msg);
      setReplyingTo(null);

      // Simulate partner response for demo
      simulatePartnerResponse(msg);
    }
    setText('');
    setShowEmojiPicker(false);
    scrollToBottom();
  };

  // Simulate partner typing and response (demo)
  const simulatePartnerResponse = (sentMsg: Message) => {
    if (!partner?.id) return;
    // Simulate delivery
    setTimeout(() => {
      useStore.getState().updateMessage(sentMsg.id, { deliveredTo: [currentUser!.id, partner.id] });
    }, 500);

    // Simulate read after 2s
    setTimeout(() => {
      useStore.getState().updateMessage(sentMsg.id, { readBy: [currentUser!.id, partner.id] });
    }, 2000);

    // Simulate partner typing and reply (demo)
    const replies = ['❤️', 'Понял!', 'Хорошо 👍', '😊', 'Ок!', 'Интересно...', 'Согласен(а)'];
    if (Math.random() > 0.5) {
      setTimeout(() => {
        useStore.getState().setTypingPartner(true);
      }, 1500);
      setTimeout(() => {
        useStore.getState().setTypingPartner(false);
        const replyMsg: Message = {
          id: crypto.randomUUID(),
          chatId: 'main',
          senderId: partner.id,
          text: replies[Math.floor(Math.random() * replies.length)],
          timestamp: new Date().toISOString(),
          edited: false,
          deleted: false,
          deletedForAll: false,
          reactions: {},
          attachments: [],
          readBy: [currentUser!.id],
          deliveredTo: [currentUser!.id, partner.id],
          pinned: false,
          replyTo: sentMsg.id,
        };
        useStore.getState().addMessage(replyMsg);
        scrollToBottom();
      }, 3000 + Math.random() * 2000);
    }
  };

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // File handling
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    Array.from(files).forEach(file => {
      const url = URL.createObjectURL(file);
      const type = file.type.startsWith('image/') ? 'image' :
                   file.type.startsWith('video/') ? 'video' : 'file';
      const attachment: Attachment = {
        id: crypto.randomUUID(),
        type: type as Attachment['type'],
        name: file.name,
        url,
        size: file.size,
        mimeType: file.type,
        expired: false,
      };
      const msg: Message = {
        id: crypto.randomUUID(),
        chatId: 'main',
        senderId: currentUser!.id,
        text: '',
        timestamp: new Date().toISOString(),
        edited: false,
        deleted: false,
        deletedForAll: false,
        reactions: {},
        attachments: [attachment],
        readBy: [],
        deliveredTo: [currentUser!.id],
        pinned: false,
      };
      addMessage(msg);
    });
    e.target.value = '';
    scrollToBottom();
  };

  // Voice recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      recordingChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordingChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(recordingChunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        const attachment: Attachment = {
          id: crypto.randomUUID(),
          type: 'voice',
          name: 'Голосовое сообщение',
          url,
          size: blob.size,
          mimeType: 'audio/webm',
          duration: recordingTime,
          expired: false,
        };
        const msg: Message = {
          id: crypto.randomUUID(),
          chatId: 'main',
          senderId: currentUser!.id,
          text: '',
          timestamp: new Date().toISOString(),
          edited: false,
          deleted: false,
          deletedForAll: false,
          reactions: {},
          attachments: [attachment],
          readBy: [],
          deliveredTo: [currentUser!.id],
          pinned: false,
          voiceDuration: recordingTime,
        };
        addMessage(msg);
        scrollToBottom();
        stream.getTracks().forEach(t => t.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      recordingTimerRef.current = window.setInterval(() => {
        setRecordingTime(t => t + 1);
      }, 1000);
    } catch (err) {
      alert('Не удалось получить доступ к микрофону. Проверьте разрешения.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
    if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    setRecordingTime(0);
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      recordingChunksRef.current = [];
    }
    setIsRecording(false);
    if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    setRecordingTime(0);
  };

  // Delete message
  const handleDelete = (msg: Message, forAll: boolean) => {
    if (forAll) {
      if (!confirm('Удалить сообщение у обоих?')) return;
    }
    deleteMessage(msg.id, forAll);
  };

  // Media click
  const handleMediaClick = (url: string, type: string) => {
    setMediaViewer(true, { url, type, index: 0 });
  };

  // Date grouping
  const getDateLabel = (dateStr: string) => {
    const date = parseISO(dateStr);
    if (isToday(date)) return 'Сегодня';
    if (isYesterday(date)) return 'Вчера';
    return format(date, 'd MMMM yyyy', { locale: ru });
  };

  // Group messages by date
  const groupedMessages: { date: string; messages: Message[] }[] = [];
  messages.forEach(msg => {
    const dateLabel = getDateLabel(msg.timestamp);
    const last = groupedMessages[groupedMessages.length - 1];
    if (last && last.date === dateLabel) {
      last.messages.push(msg);
    } else {
      groupedMessages.push({ date: dateLabel, messages: [msg] });
    }
  });

  // Search filter
  const filteredMessages = searchQuery
    ? messages.filter(m => m.text.toLowerCase().includes(searchQuery.toLowerCase()))
    : null;

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${String(s).padStart(2, '0')}`;
  };

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <header className="flex items-center gap-3 px-3 sm:px-4 py-3 border-b" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
        <button className="mobile-only p-2 rounded-full hover:opacity-70" onClick={() => setActiveView('chat')}>
          <Settings size={20} style={{ color: 'var(--text-secondary)' }} />
        </button>
        <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold" style={{ background: 'var(--accent)' }}>
          {partner?.displayName?.[0]?.toUpperCase() || '?'}
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="font-semibold text-[15px] truncate" style={{ color: 'var(--text-primary)' }}>
            {partner?.displayName || 'Партнёр'}
          </h2>
          <p className="text-xs" style={{ color: typingPartner ? 'var(--accent)' : 'var(--text-muted)' }}>
            {typingPartner ? 'печатает...' : connectionStatus === 'connected' ? 'в сети' : connectionStatus === 'connecting' ? 'подключение...' : 'не в сети'}
          </p>
        </div>
        <div className="flex items-center gap-1">
          <button className="p-2 rounded-full hover:opacity-70 desktop-only" style={{ color: 'var(--text-secondary)' }}>
            <Phone size={18} />
          </button>
          <button className="p-2 rounded-full hover:opacity-70 desktop-only" style={{ color: 'var(--text-secondary)' }}>
            <Video size={18} />
          </button>
          <button className="p-2 rounded-full hover:opacity-70" onClick={() => setSearchOpen(!searchOpen)} style={{ color: 'var(--text-secondary)' }}>
            <Search size={18} />
          </button>
          <button className="p-2 rounded-full hover:opacity-70" onClick={() => setActiveView('settings')} style={{ color: 'var(--text-secondary)' }}>
            <MoreVertical size={18} />
          </button>
        </div>
      </header>

      {/* Connection status */}
      {connectionStatus !== 'connected' && (
        <div className="px-4 py-2 text-center text-xs" style={{ background: connectionStatus === 'connecting' ? 'var(--warning)' : 'var(--danger)', color: 'white' }}>
          {connectionStatus === 'connecting' ? '🟡 Подключение...' : '🔴 Нет соединения'}
        </div>
      )}

      {/* Search bar */}
      {searchOpen && (
        <div className="px-3 py-2 border-b flex items-center gap-2" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
          <input
            type="text"
            placeholder="Поиск сообщений..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="flex-1 text-sm"
            autoFocus
          />
          <button onClick={() => { setSearchOpen(false); setSearchQuery(''); }}>
            <X size={18} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>
      )}

      {/* Pinned message */}
      {messages.find(m => m.pinned && !m.deletedForAll) && (
        <div className="flex items-center gap-2 px-4 py-2 border-b cursor-pointer" style={{ background: 'rgba(124,92,252,0.1)', borderColor: 'var(--border)' }}
          onClick={() => {
            const pinned = messages.find(m => m.pinned && !m.deletedForAll);
            if (pinned) {
              const el = document.getElementById(`msg-${pinned.id}`);
              el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          }}>
          <Pin size={14} style={{ color: 'var(--accent)' }} />
          <p className="text-xs truncate flex-1" style={{ color: 'var(--text-primary)' }}>
            {messages.find(m => m.pinned && !m.deletedForAll)?.text}
          </p>
        </div>
      )}

      {/* Messages */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto py-2">
        {filteredMessages ? (
          // Search results
          <div className="px-3 space-y-1">
            <p className="text-xs text-center py-2" style={{ color: 'var(--text-muted)' }}>
              Найдено: {filteredMessages.length}
            </p>
            {filteredMessages.map(msg => (
              <MessageBubble
                key={msg.id}
                message={msg}
                sender={msg.senderId === currentUser?.id ? currentUser! : partner!}
                isOwn={msg.senderId === currentUser?.id}
                onReply={setReplyingTo}
                onEdit={setEditingMessage}
                onDelete={handleDelete}
                onMediaClick={handleMediaClick}
              />
            ))}
          </div>
        ) : (
          // Normal view
          groupedMessages.map((group, gi) => (
            <div key={gi}>
              <div className="sticky top-0 z-10 flex justify-center py-2">
                <span className="px-3 py-1 rounded-full text-xs font-medium" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>
                  {group.date}
                </span>
              </div>
              {group.messages.map(msg => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  sender={msg.senderId === currentUser?.id ? currentUser! : partner!}
                  isOwn={msg.senderId === currentUser?.id}
                  onReply={setReplyingTo}
                  onEdit={setEditingMessage}
                  onDelete={handleDelete}
                  onMediaClick={handleMediaClick}
                />
              ))}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Scroll to bottom button */}
      {showScrollBtn && (
        <button
          className="absolute bottom-24 right-4 w-10 h-10 rounded-full shadow-lg flex items-center justify-center"
          style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
          onClick={() => scrollToBottom()}
        >
          <ArrowDown size={18} style={{ color: 'var(--text-secondary)' }} />
        </button>
      )}

      {/* Typing indicator */}
      {typingPartner && (
        <div className="px-4 py-1">
          <div className="inline-flex items-center gap-1 px-3 py-2 rounded-2xl" style={{ background: 'var(--bg-message-in)' }}>
            <div className="typing-dots">
              <span></span><span></span><span></span>
            </div>
          </div>
        </div>
      )}

      {/* Reply/Edit bar */}
      {(replyingTo || editingMessage) && (
        <div className="flex items-center gap-2 px-4 py-2 border-t" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium" style={{ color: 'var(--accent)' }}>
              {editingMessage ? '✏️ Редактирование' : `↩️ Ответ ${replyingTo?.senderId === currentUser?.id ? 'себе' : partner?.displayName}`}
            </p>
            <p className="text-xs truncate" style={{ color: 'var(--text-secondary)' }}>
              {editingMessage?.text || replyingTo?.text}
            </p>
          </div>
          <button onClick={() => { setReplyingTo(null); setEditingMessage(null); }}>
            <X size={18} style={{ color: 'var(--text-muted)' }} />
          </button>
        </div>
      )}

      {/* Recording indicator */}
      {isRecording && (
        <div className="flex items-center gap-3 px-4 py-3 border-t" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
          <div className="recording-indicator" />
          <span className="text-sm font-mono" style={{ color: 'var(--danger)' }}>{formatTime(recordingTime)}</span>
          <div className="flex-1" />
          <button onClick={cancelRecording} className="btn btn-secondary text-sm px-3 py-1.5">Отмена</button>
          <button onClick={stopRecording} className="btn btn-primary text-sm px-3 py-1.5">Отправить</button>
        </div>
      )}

      {/* Input area */}
      {!isRecording && (
        <div className="flex items-end gap-2 px-3 sm:px-4 py-2 border-t" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)', paddingBottom: 'max(8px, var(--safe-bottom))' }}>
          {/* Attach button */}
          <div className="relative">
            <button className="p-2 rounded-full hover:opacity-70" style={{ color: 'var(--text-secondary)' }} onClick={() => fileInputRef.current?.click()}>
              <Paperclip size={22} />
            </button>
            <input ref={fileInputRef} type="file" multiple accept="image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx,.zip,.txt" className="hidden" onChange={handleFileSelect} />
          </div>

          {/* Camera button (mobile) */}
          <button className="p-2 rounded-full hover:opacity-70 mobile-only" style={{ color: 'var(--text-secondary)' }} onClick={() => cameraInputRef.current?.click()}>
            <Camera size={22} />
          </button>
          <input ref={cameraInputRef} type="file" accept="image/*,video/*" capture="environment" className="hidden" onChange={handleFileSelect} />

          {/* Text input */}
          <div className="flex-1 relative">
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Сообщение..."
              rows={1}
              className="resize-none max-h-[120px] py-2.5"
              style={{ minHeight: '40px' }}
            />
            {/* Emoji button */}
            <button
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-full hover:opacity-70"
              style={{ color: 'var(--text-muted)' }}
              onClick={() => setShowEmojiPicker(!showEmojiPicker)}
            >
              <Smile size={20} />
            </button>
          </div>

          {/* Send / Mic */}
          {text.trim() ? (
            <button className="p-2 rounded-full" style={{ background: 'var(--accent)', color: 'white' }} onClick={sendMessage}>
              <Send size={20} />
            </button>
          ) : (
            <button className="p-2 rounded-full hover:opacity-70" style={{ color: 'var(--text-secondary)' }} onClick={startRecording}>
              <Mic size={22} />
            </button>
          )}
        </div>
      )}

      {/* Emoji picker */}
      {showEmojiPicker && (
        <div className="absolute bottom-20 left-2 right-2 sm:left-auto sm:right-4 sm:w-[320px] z-50 rounded-xl overflow-hidden shadow-xl border" style={{ borderColor: 'var(--border)' }}>
          <EmojiPicker
            onEmojiClick={(emoji) => setText(prev => prev + emoji.emoji)}
            width="100%"
            height="350px"
            
          />
        </div>
      )}
    </div>
  );
}
