/**
 * API Service for ПриватЧат
 * Handles all HTTP communication with the backend
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

class ApiService {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('pc_token', token);
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('pc_token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('pc_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.clearToken();
      window.location.href = '/';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async register(username: string, password: string, displayName: string) {
    return this.request<{ token: string; user: any; invite_code: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, display_name: displayName }),
    });
  }

  async registerWithInvite(username: string, password: string, displayName: string, inviteCode: string) {
    return this.request<{ token: string; user: any }>('/api/auth/register-with-invite', {
      method: 'POST',
      body: JSON.stringify({ username, password, display_name: displayName, invite_code: inviteCode }),
    });
  }

  async login(username: string, password: string) {
    return this.request<{ token: string; user: any }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async logout() {
    return this.request('/api/auth/logout', { method: 'POST' });
  }

  async changePassword(oldPassword: string, newPassword: string) {
    return this.request('/api/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });
  }

  // Users
  async getMe() {
    return this.request<any>('/api/users/me');
  }

  async getPartner() {
    return this.request<any>('/api/users/partner');
  }

  async updateProfile(data: { display_name?: string; bio?: string; username?: string }) {
    return this.request('/api/users/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async uploadAvatar(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const token = this.getToken();
    const response = await fetch(`${API_BASE}/api/users/me/avatar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    return response.json();
  }

  // Messages
  async getMessages(limit = 50, before?: string) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (before) params.set('before', before);
    return this.request<any[]>(`/api/messages?${params}`);
  }

  async sendMessage(text: string, replyTo?: string) {
    return this.request('/api/messages', {
      method: 'POST',
      body: JSON.stringify({ text, reply_to: replyTo }),
    });
  }

  async editMessage(messageId: string, text: string) {
    return this.request(`/api/messages/${messageId}`, {
      method: 'PUT',
      body: JSON.stringify({ text }),
    });
  }

  async deleteMessage(messageId: string, forAll = false) {
    return this.request(`/api/messages/${messageId}?for_all=${forAll}`, {
      method: 'DELETE',
    });
  }

  async toggleReaction(messageId: string, emoji: string) {
    const formData = new FormData();
    formData.append('emoji', emoji);
    const token = this.getToken();
    const response = await fetch(`${API_BASE}/api/messages/${messageId}/reactions`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    return response.json();
  }

  async markAsRead(messageId: string) {
    return this.request(`/api/messages/${messageId}/read`, { method: 'POST' });
  }

  // Files
  async uploadFile(file: File, messageId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (messageId) formData.append('message_id', messageId);
    const token = this.getToken();
    const response = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    return response.json();
  }

  // Search
  async search(query: string, type?: string) {
    const params = new URLSearchParams({ q: query });
    if (type) params.set('type', type);
    return this.request<any[]>(`/api/search?${params}`);
  }

  // Push
  async subscribePush(subscription: { endpoint: string; p256dh: string; auth: string }) {
    return this.request('/api/push/subscribe', {
      method: 'POST',
      body: JSON.stringify(subscription),
    });
  }
}

export const api = new ApiService();
