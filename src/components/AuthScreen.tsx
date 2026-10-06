import { useState } from 'react';
import { useStore } from '../stores';
import { api } from '../services/api';
import { wsService } from '../services/websocket';
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

    try {
      if (mode === 'login') {
        const response = await api.login(username, password);
        const partner = await api.getPartner();
        
        if (!partner) {
          setError('Partner has not registered yet');
          setLoading(false);
          return;
        }
        
        login(response.user, partner);
        wsService.connect();
        
      } else if (mode === 'register') {
        if (!username || !password || !displayName) {
          setError('Fill in all fields');
          setLoading(false);
          return;
        }
        if (username.length < 3) {
          setError('Username must be at least 3 characters');
          setLoading(false);
          return;
        }
        if (password.length < 6) {
          setError('Password must be at least 6 characters');
          setLoading(false);
          return;
        }
        
        const response = await api.register(username, password, displayName);
        const partner = await api.getPartner();
        
        login(response.user, partner || { id: '', username: '', displayName: 'Waiting for partner...', online: false, lastSeen: '' });
        wsService.connect();
        
        alert(`Your invite code: ${response.invite_code}\n\nSend it to your partner.`);
        
      } else if (mode === 'invite') {
        if (!username || !password || !displayName || !inviteCode) {
          setError('Fill in all fields');
          setLoading(false);
          return;
        }
        
        const response = await api.registerWithInvite(username, password, displayName, inviteCode);
        const partner = await api.getPartner();
        
        login(response.user, partner);
        wsService.connect();
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
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
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Private messenger for two</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'invite' && (
            <div className="relative">
              <Key size={18} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Invite code"
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
              placeholder="Username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="pl-10"
              autoComplete="username"
            />
          </div>

          {(mode === 'register' || mode === 'invite') && (
            <input
              type="text"
              placeholder="Display name"
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
            />
          )}

          <div className="relative">
            <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
            <input
              type="password"
              placeholder="Password"
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
            {loading ? '...' : mode === 'login' ? 'Login' : mode === 'register' ? 'Create account' : 'Join'}
          </button>
        </form>

        <div className="mt-6 text-center space-y-2">
          {mode === 'login' && (
            <>
              <button onClick={() => { setMode('register'); setError(''); }} className="text-sm block mx-auto" style={{ color: 'var(--accent)' }}>
                Create account
              </button>
              <button onClick={() => { setMode('invite'); setError(''); }} className="text-sm block mx-auto" style={{ color: 'var(--accent)' }}>
                Join with invite code
              </button>
            </>
          )}
          {(mode === 'register' || mode === 'invite') && (
            <button onClick={() => { setMode('login'); setError(''); }} className="text-sm block mx-auto" style={{ color: 'var(--accent)' }}>
              Already have an account? Login
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
