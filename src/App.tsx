import { useEffect } from 'react';
import { useStore } from './stores';
import { api } from './services/api';
import { wsService } from './services/websocket';
import AuthScreen from './components/AuthScreen';
import ChatView from './components/ChatView';
import SettingsView from './components/SettingsView';
import MediaViewer from './components/MediaViewer';

export default function App() {
  const { isAuthenticated, activeView, theme, setConnectionStatus, login, logout } = useStore();

  // Theme management
  useEffect(() => {
    const resolvedTheme = theme === 'system'
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : theme;

    document.documentElement.className = resolvedTheme;
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [theme]);

  // Listen for system theme changes
  useEffect(() => {
    if (theme !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => {
      const resolved = mq.matches ? 'dark' : 'light';
      document.documentElement.className = resolved;
      document.documentElement.style.colorScheme = resolved;
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  // Initialize WebSocket and load user data on mount
  useEffect(() => {
    if (!isAuthenticated) return;

    const init = async () => {
      try {
        // Load user data from server
        const [me, partner] = await Promise.all([
          api.getMe(),
          api.getPartner()
        ]);

        if (!me) {
          logout();
          return;
        }

        // Update store with server data
        login(me, partner);

        // Connect WebSocket
        wsService.connect();
      } catch (error) {
        console.error('Failed to initialize:', error);
        logout();
      }
    };

    init();

    return () => {
      wsService.disconnect();
    };
  }, [isAuthenticated, login, logout]);

  // Handle online/offline events
  useEffect(() => {
    if (!isAuthenticated) return;
    
    const handleOnline = () => setConnectionStatus('connected');
    const handleOffline = () => setConnectionStatus('disconnected');
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Initial status
    setConnectionStatus(navigator.onLine ? 'connected' : 'disconnected');
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isAuthenticated, setConnectionStatus]);

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  return (
    <div className="h-full flex" style={{ background: 'var(--bg-primary)' }}>
      {/* Desktop sidebar */}
      <aside className="desktop-only w-[320px] border-r flex flex-col" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
        <div className="p-4 border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold overflow-hidden" style={{ background: 'var(--accent)' }}>
              {useStore.getState().currentUser?.avatar ? (
                <img src={useStore.getState().currentUser!.avatar} alt="" className="w-full h-full object-cover" />
              ) : (
                useStore.getState().currentUser?.displayName?.[0]?.toUpperCase() || '?'
              )}
            </div>
            <div className="flex-1">
              <h2 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>ПриватЧат</h2>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{useStore.getState().currentUser?.displayName}</p>
            </div>
          </div>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center p-4">
          <div className="w-20 h-20 rounded-full flex items-center justify-center text-white text-2xl font-bold mb-3" style={{ background: 'var(--accent)' }}>
            {useStore.getState().partner?.displayName?.[0]?.toUpperCase() || '?'}
          </div>
          <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>
            {useStore.getState().partner?.displayName || 'Partner'}
          </h3>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Your only chat</p>
        </div>
        <div className="p-3 border-t" style={{ borderColor: 'var(--border)' }}>
          <button
            className="w-full btn btn-secondary text-sm"
            onClick={() => useStore.getState().setActiveView('settings')}
          >
            ⚙️ Settings
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 h-full relative">
        {activeView === 'chat' && <ChatView />}
        {activeView === 'settings' && <SettingsView />}
      </main>

      {/* Media viewer overlay */}
      <MediaViewer />
    </div>
  );
}
