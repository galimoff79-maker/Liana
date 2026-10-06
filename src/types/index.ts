export interface User {
  id: string;
  username: string;
  displayName: string;
  avatar?: string;
  bio?: string;
  online: boolean;
  lastSeen: string;
}

export interface Message {
  id: string;
  chatId: string;
  senderId: string;
  text: string;
  timestamp: string;
  edited: boolean;
  editedAt?: string;
  deleted: boolean;
  deletedForAll: boolean;
  replyTo?: string;
  forwardedFrom?: string;
  reactions: Record<string, string[]>;
  attachments: Attachment[];
  readBy: string[];
  deliveredTo: string[];
  pinned: boolean;
  voiceDuration?: number;
}

export interface Attachment {
  id: string;
  type: 'image' | 'video' | 'voice' | 'file';
  name: string;
  url: string;
  thumbnailUrl?: string;
  size: number;
  mimeType: string;
  duration?: number;
  width?: number;
  height?: number;
  expired: boolean;
}

export interface Session {
  id: string;
  device: string;
  browser: string;
  os: string;
  lastActive: string;
  current: boolean;
}

export interface NotificationSettings {
  push: boolean;
  sound: boolean;
  vibration: boolean;
  preview: boolean;
  whenOpen: boolean;
}

export interface UserSettings {
  theme: 'light' | 'dark' | 'system';
  notifications: NotificationSettings;
}

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';
