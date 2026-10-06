import { useState } from 'react';
import { useStore } from '../stores';
import { Lock, User, MessageCircle, Key } from 'lucide-react';

export default function AuthScreen() {
  const [mode, setMode] = useState<'login' | 'register' | 'invite'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Demo auth - in production this connects to backend API
    await new Promise(r => setTimeout(r, 500));

    if (mode === 'login') {
      const savedUser = localStorage.getItem('pc_auth_' + username);
      if (!savedUser) {
        setError('Пользователь не найден');
        setLoading(false);
        return;
      }
      const auth = JSON.parse(savedUser);
      if (auth.password !== password) {
        setError('Неверный пароль');
        setLoading(false);
        return;
      }
      const partnerData = localStorage.getItem('pc_partner_data');
      if (!partnerData) {
        setError('Партнёр ещё не зарегистрирован');
        setLoading(false);
        return;
      }
      const partner = JSON.parse(partnerData);
      login(auth.user, partner);
    } else if (mode === 'register') {
      if (!username || !password || !displayName) {
        setError('Заполните все поля');
        setLoading(false);
        return;
      }
      if (username.length < 3) {
        setError('Имя пользователя минимум 3 символа');
        setLoading(false);
        return;
      }
      if (password.length < 6) {
        setError('Пароль минимум 6 символов');
        setLoading(false);
        return;
      }
      const existing = localStorage.getItem('pc_auth_' + username);
      if (existing) {
        setError('Пользователь уже существует');
        setLoading(false);
        return;
      }
      // Check if first user already exists
      const firstUserExists = Object.keys(localStorage).some(k => k.startsWith('pc_auth_'));
      if (firstUserExists) {
        setError('Регистрация закрыта. Используйте код-приглашение.');
        setLoading(false);
        return;
      }
      const user = {
        id: crypto.randomUUID(),
        username,
        displayName,
        online: true,
        lastSeen: new Date().toISOString(),
      };
      localStorage.setItem('pc_auth_' + username, JSON.stringify({ user, password }));
      // Generate invite code
      const invite = crypto.randomUUID().slice(0, 8).toUpperCase();
      localStorage.setItem('pc_invite', invite);
      login(user, { id: '', username: '', displayName: 'Ожидание партнёра...', online: false, lastSeen: '' });
      alert(`Ваш код-приглашение: ${invite}\n\nОтправьте его вашему собеседнику.`);
    } else if (mode === 'invite') {
      if (!username || !password || !displayName || !inviteCode) {
        setError('Заполните все поля');
        setLoading(false);
        return;
      }
      const savedInvite = localStorage.getItem('pc_invite');
      if (savedInvite !== inviteCode.toUpperCase()) {
        setError('Неверный код-приглашение');
        setLoading(false);
        return;
      }
      const existing = localStorage.getItem('pc_auth_' + username);
      if (existing) {
        setError('Пользователь уже существует');
        setLoading(false);
        return;
      }
      const user = {
        id: crypto.randomUUID(),
        username,
        displayName,
        online: true,
        lastSeen: new Date().toISOString(),
      };
      localStorage.setItem('pc_auth_' + username, JSON.stringify({ user, password }));
      localStorage.removeItem('pc_invite');
      // Find first user as partner
      const keys = Object.keys(localStorage).filter(k => k.startsWith('pc_auth_') && k !== 'pc_auth_' + username);
      if (keys.length === 0) {
        setError('Код-приглашение недействителен');
        setLoading(false);
        return;
      }
      const partnerAuth = JSON.parse(localStorage.getItem(keys[0])!);
      localStorage.setItem('pc_partner_data', JSON.stringify(partnerAuth.user));
      login(user, partnerAuth.user);
    }
    setLoading(false);
  };

  return (
    <div className="h-full flex items-center justify-center p-4" style={{ background: 'var(--bg-primary)' }}>
      <div className="w-full max-w-sm animate-fade-in">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center" style={{ background: 'var(--accent)' }}>
            <MessageCircle size={32} color="white" />
          </div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>ПриватЧат</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Приватный мессенджер для двоих</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'invite' && (
            <div className="relative">
              <Key size={18} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Код-приглашение"
                value={inviteCode}
                onChange={e => setInviteCode(e.target.value)}
                className="pl-10 uppercase tracking-wider text-center font-mono"
                maxLength={8}
              />
            </div>
          )}

          <div className="relative">
            <User size={18} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Имя пользователя"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="pl-10"
              autoComplete="username"
            />
          </div>

          {(mode === 'register' || mode === 'invite') && (
            <input
              type="text"
              placeholder="Отображаемое имя"
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
            />
          )}

          <div className="relative">
            <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
            <input
              type="password"
              placeholder="Пароль"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="pl-10"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {error && (
            <p className="text-sm text-center" style={{ color: 'var(--danger)' }}>{error}</p>
          )}

          <button type="submit" disabled={loading} className="btn btn-primary w-full">
            {loading ? '...' : mode === 'login' ? 'Войти' : mode === 'register' ? 'Создать аккаунт' : 'Присоединиться'}
          </button>
        </form>

        <div className="mt-6 text-center space-y-2">
          {mode === 'login' && (
            <>
              <button onClick={() => { setMode('register'); setError(''); }} className="text-sm block mx-auto" style={{ color: 'var(--accent)' }}>
                Создать аккаунт
              </button>
              <button onClick={() => { setMode('invite'); setError(''); }} className="text-sm block mx-auto" style={{ color: 'var(--accent)' }}>
                Войти по коду-приглашению
              </button>
            </>
          )}
          {(mode === 'register' || mode === 'invite') && (
            <button onClick={() => { setMode('login'); setError(''); }} className="text-sm block mx-auto" style={{ color: 'var(--accent)' }}>
              Уже есть аккаунт? Войти
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
