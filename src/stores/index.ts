import { create } from 'zustand';
import type { User, Message, ConnectionStatus, Session, UserSettings } from '../types';

interface AppState {
  // Auth
  currentUser: User | null;
  partner: User | null;
  isAuthenticated: boolean;
  
  // Messages
  messages: Message[];
  
  // Connection
  connectionStatus: ConnectionStatus;
  
  // UI
  theme: 'light' | 'dark' | 'system';
  activeView: 'chat' | 'settings' | 'search' | 'profile';
  replyingTo: Message | null;
  editingMessage: Message | null;
  showEmojiPicker: boolean;
  showMediaViewer: boolean;
  selectedMedia: { url: string; type: string; index: number } | null;
  isRecording: boolean;
  recordingTime: number;
  typingPartner: boolean;
  
  // Sessions
  sessions: Session[];
  
  // Settings
  settings: UserSettings;
  
  // Actions
  login: (user: User, partner: User) => void;
  logout: () => void;
  addMessage: (msg: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  deleteMessage: (id: string, forAll: boolean) => void;
  addReaction: (messageId: string, emoji: string, userId: string) => void;
  removeReaction: (messageId: string, emoji: string, userId: string) => void;
  markAsRead: (messageIds: string[]) => void;
  setConnectionStatus: (status: ConnectionStatus) => void;
  setActiveView: (view: 'chat' | 'settings' | 'search' | 'profile') => void;
  setReplyingTo: (msg: Message | null) => void;
  setEditingMessage: (msg: Message | null) => void;
  setShowEmojiPicker: (show: boolean) => void;
  setMediaViewer: (show: boolean, media?: { url: string; type: string; index: number }) => void;
  setTypingPartner: (typing: boolean) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  updateSettings: (settings: Partial<UserSettings>) => void;
  updateProfile: (updates: Partial<User>) => void;
  setSessions: (sessions: Session[]) => void;
}

const loadFromStorage = <T>(key: string, fallback: T): T => {
  try {
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : fallback;
  } catch { return fallback; }
};

const saveToStorage = (key: string, value: unknown) => {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
};

export const useStore = create<AppState>((set, get) => ({
  currentUser: loadFromStorage('pc_user', null),
  partner: loadFromStorage('pc_partner', null),
  isAuthenticated: !!loadFromStorage('pc_user', null),
  messages: loadFromStorage('pc_messages', []),
  connectionStatus: 'disconnected',
  theme: loadFromStorage('pc_theme', 'dark'),
  activeView: 'chat',
  replyingTo: null,
  editingMessage: null,
  showEmojiPicker: false,
  showMediaViewer: false,
  selectedMedia: null,
  isRecording: false,
  recordingTime: 0,
  typingPartner: false,
  sessions: [],
  settings: loadFromStorage('pc_settings', {
    theme: 'dark',
    notifications: { push: true, sound: true, vibration: true, preview: true, whenOpen: false }
  }),

  login: (user, partner) => {
    saveToStorage('pc_user', user);
    saveToStorage('pc_partner', partner);
    set({ currentUser: user, partner, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('pc_user');
    localStorage.removeItem('pc_partner');
    set({ currentUser: null, partner: null, isAuthenticated: false, messages: [] });
  },

  addMessage: (msg) => {
    const messages = [...get().messages, msg];
    saveToStorage('pc_messages', messages);
    set({ messages });
  },

  updateMessage: (id, updates) => {
    const messages = get().messages.map(m => m.id === id ? { ...m, ...updates } : m);
    saveToStorage('pc_messages', messages);
    set({ messages });
  },

  deleteMessage: (id, forAll) => {
    const messages = get().messages.map(m => {
      if (m.id !== id) return m;
      if (forAll) return { ...m, deleted: true, deletedForAll: true, text: '', attachments: [] };
      return m;
    }).filter(m => !forAll || m.id !== id || m.deletedForAll);
    saveToStorage('pc_messages', messages);
    set({ messages });
  },

  addReaction: (messageId, emoji, userId) => {
    const messages = get().messages.map(m => {
      if (m.id !== messageId) return m;
      const reactions = { ...m.reactions };
      if (!reactions[emoji]) reactions[emoji] = [];
      if (!reactions[emoji].includes(userId)) reactions[emoji] = [...reactions[emoji], userId];
      return { ...m, reactions };
    });
    saveToStorage('pc_messages', messages);
    set({ messages });
  },

  removeReaction: (messageId, emoji, userId) => {
    const messages = get().messages.map(m => {
      if (m.id !== messageId) return m;
      const reactions = { ...m.reactions };
      if (reactions[emoji]) {
        reactions[emoji] = reactions[emoji].filter(id => id !== userId);
        if (reactions[emoji].length === 0) delete reactions[emoji];
      }
      return { ...m, reactions };
    });
    saveToStorage('pc_messages', messages);
    set({ messages });
  },

  markAsRead: (messageIds) => {
    const userId = get().currentUser?.id;
    if (!userId) return;
    const messages = get().messages.map(m => {
      if (!messageIds.includes(m.id)) return m;
      const readBy = m.readBy.includes(userId) ? m.readBy : [...m.readBy, userId];
      return { ...m, readBy };
    });
    saveToStorage('pc_messages', messages);
    set({ messages });
  },

  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setActiveView: (view) => set({ activeView: view }),
  setReplyingTo: (msg) => set({ replyingTo: msg }),
  setEditingMessage: (msg) => set({ editingMessage: msg }),
  setShowEmojiPicker: (show) => set({ showEmojiPicker: show }),
  setMediaViewer: (show, media) => set({ showMediaViewer: show, selectedMedia: media || null }),
  setTypingPartner: (typing) => set({ typingPartner: typing }),
  setTheme: (theme) => { saveToStorage('pc_theme', theme); set({ theme }); },
  updateSettings: (updates) => {
    const settings = { ...get().settings, ...updates };
    saveToStorage('pc_settings', settings);
    set({ settings });
  },
  updateProfile: (updates) => {
    const user = get().currentUser;
    if (!user) return;
    const updated = { ...user, ...updates };
    saveToStorage('pc_user', updated);
    set({ currentUser: updated });
  },
  setSessions: (sessions) => set({ sessions }),
}));
