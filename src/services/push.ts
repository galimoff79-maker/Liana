/**
 * Push Notification Service for ПриватЧат
 */

import { api } from './api';

class PushService {
  private registration: ServiceWorkerRegistration | null = null;

  async init() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.log('Push notifications not supported');
      return false;
    }

    try {
      this.registration = await navigator.serviceWorker.ready;
      return true;
    } catch (e) {
      console.error('SW not ready:', e);
      return false;
    }
  }

  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) return false;
    
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  async subscribe() {
    if (!this.registration) {
      const ready = await this.init();
      if (!ready) return null;
    }

    try {
      const vapidKey = import.meta.env.VITE_VAPID_PUBLIC_KEY || '';
      const subscription = await this.registration!.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: vapidKey ? this.urlBase64ToUint8Array(vapidKey) as any : undefined,
      });

      const json = subscription.toJSON();
      const p256dh = json.keys?.p256dh || '';
      const auth = json.keys?.auth || '';
      await api.subscribePush({
        endpoint: json.endpoint!,
        p256dh: btoa(String.fromCharCode(...new Uint8Array(p256dh as any))),
        auth: btoa(String.fromCharCode(...new Uint8Array(auth as any))),
      });

      return subscription;
    } catch (e) {
      console.error('Push subscription failed:', e);
      return null;
    }
  }

  async unsubscribe() {
    if (!this.registration) return;
    const subscription = await this.registration.pushManager.getSubscription();
    if (subscription) {
      await subscription.unsubscribe();
    }
  }

  showLocalNotification(title: string, body: string, data?: any) {
    if (Notification.permission !== 'granted') return;
    
    const notification = new Notification(title, {
      body,
      icon: '/icon.svg',
      badge: '/icon.svg',
      tag: 'message',
      data,
    });

    notification.onclick = () => {
      window.focus();
      notification.close();
    };
  }

  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    if (!base64String) return new Uint8Array();
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    return new Uint8Array([...rawData].map(char => char.charCodeAt(0)));
  }
}

export const pushService = new PushService();
