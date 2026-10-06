/**
 * WebSocket Service for ПриватЧат
 * Handles real-time communication with the backend
 */

import { useStore } from '../stores';

type MessageHandler = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private messageQueue: any[] = [];

  connect(token: string) {
    const wsUrl = (import.meta.env.VITE_WS_URL || `ws${location.protocol === 'https:' ? 's' : ''}://${location.host}`) + `/ws?token=${token}`;
    
    try {
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        useStore.getState().setConnectionStatus('connected');
        this.startHeartbeat();
        this.flushQueue();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      this.ws.onclose = (event) => {
        this.stopHeartbeat();
        useStore.getState().setConnectionStatus('disconnected');
        if (event.code !== 4001) { // Not auth error
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = () => {
        useStore.getState().setConnectionStatus('disconnected');
      };
    } catch (e) {
      useStore.getState().setConnectionStatus('disconnected');
      this.scheduleReconnect();
    }
  }

  private handleMessage(data: any) {
    const { type } = data;
    
    // Update store based on message type
    const store = useStore.getState();
    
    switch (type) {
      case 'pong':
        break;
      case 'new_message':
        store.addMessage(data.message);
        break;
      case 'message_edited':
        store.updateMessage(data.messageId, { text: data.text, edited: true, editedAt: data.editedAt });
        break;
      case 'message_deleted':
        store.deleteMessage(data.messageId, true);
        break;
      case 'reaction_updated':
        store.updateMessage(data.messageId, { reactions: data.reactions });
        break;
      case 'typing':
        store.setTypingPartner(data.isTyping);
        break;
      case 'user_online':
        if (store.partner) {
          store.partner.online = true;
        }
        break;
      case 'user_offline':
        if (store.partner) {
          store.partner.online = false;
          store.partner.lastSeen = data.lastSeen;
        }
        break;
      case 'message_read':
        store.updateMessage(data.messageId, { 
          readBy: [...new Set([...(store.messages.find(m => m.id === data.messageId)?.readBy || []), data.userId])] 
        });
        break;
    }

    // Call registered handlers
    const handlers = this.handlers.get(type) || [];
    handlers.forEach(h => h(data));
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      this.messageQueue.push(data);
    }
  }

  sendTyping(isTyping: boolean) {
    this.send({ type: 'typing', isTyping });
  }

  private flushQueue() {
    while (this.messageQueue.length > 0) {
      const msg = this.messageQueue.shift();
      this.send(msg);
    }
  }

  private startHeartbeat() {
    this.heartbeatTimer = window.setInterval(() => {
      this.send({ type: 'ping' });
    }, 30000);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    
    useStore.getState().setConnectionStatus('connecting');
    
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    
    this.reconnectTimer = window.setTimeout(() => {
      const token = localStorage.getItem('pc_token');
      if (token) this.connect(token);
    }, delay);
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000);
      this.ws = null;
    }
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) this.handlers.set(type, []);
    this.handlers.get(type)!.push(handler);
  }

  off(type: string, handler: MessageHandler) {
    const handlers = this.handlers.get(type);
    if (handlers) {
      const idx = handlers.indexOf(handler);
      if (idx >= 0) handlers.splice(idx, 1);
    }
  }
}

export const wsService = new WebSocketService();
