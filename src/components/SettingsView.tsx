import { useState } from 'react';
import { ArrowLeft, User, Bell, Palette, Shield, LogOut, Monitor, Smartphone, Trash2, Key, Camera } from 'lucide-react';
import { useStore } from '../stores';

export default function SettingsView() {
  const { currentUser, settings, sessions, setActiveView, setTheme, updateSettings, updateProfile, logout, setSessions } = useStore();
  const [editName, setEditName] = useState(false);
  const [newName, setNewName] = useState(currentUser?.displayName || '');
  const [editUsername, setEditUsername] = useState(false);
  const [newUsername, setNewUsername] = useState(currentUser?.username || '');
  const [editBio, setEditBio] = useState(false);
  const [newBio, setNewBio] = useState(currentUser?.bio || '');
  const [editPassword, setEditPassword] = useState(false);
  const [oldPass, setOldPass] = useState('');
  const [newPass, setNewPass] = useState('');

  const handleSaveName = () => {
    if (newName.trim()) {
      updateProfile({ displayName: newName.trim() });
      setEditName(false);
    }
  };

  const handleSaveUsername = () => {
    if (newUsername.trim() && newUsername.length >= 3) {
      updateProfile({ username: newUsername.trim() });
      setEditUsername(false);
    }
  };

  const handleSaveBio = () => {
    updateProfile({ bio: newBio.trim() });
    setEditBio(false);
  };

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      updateProfile({ avatar: url });
    }
  };

  const handleLogout = () => {
    if (confirm('Выйти из аккаунта?')) {
      logout();
    }
  };

  const resolvedTheme = settings.theme === 'system'
    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : settings.theme;

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <header className="flex items-center gap-3 px-4 py-3 border-b" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
        <button onClick={() => setActiveView('chat')} className="p-2 rounded-full hover:opacity-70">
          <ArrowLeft size={20} style={{ color: 'var(--text-primary)' }} />
        </button>
        <h1 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Настройки</h1>
      </header>

      <div className="flex-1 overflow-y-auto">
        {/* Profile section */}
        <div className="p-4">
          <div className="flex items-center gap-4 mb-6">
            <div className="relative">
              <div className="w-16 h-16 rounded-full flex items-center justify-center text-white text-xl font-bold overflow-hidden" style={{ background: 'var(--accent)' }}>
                {currentUser?.avatar ? (
                  <img src={currentUser.avatar} alt="" className="w-full h-full object-cover" />
                ) : (
                  currentUser?.displayName?.[0]?.toUpperCase() || '?'
                )}
              </div>
              <label className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full flex items-center justify-center cursor-pointer" style={{ background: 'var(--accent)' }}>
                <Camera size={14} color="white" />
                <input type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
              </label>
            </div>
            <div className="flex-1">
              <h2 className="font-semibold text-lg" style={{ color: 'var(--text-primary)' }}>{currentUser?.displayName}</h2>
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>@{currentUser?.username}</p>
            </div>
          </div>

          {/* Account settings */}
          <div className="space-y-3">
            <div className="p-3 rounded-xl" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <User size={18} style={{ color: 'var(--accent)' }} />
                  <span className="text-sm" style={{ color: 'var(--text-primary)' }}>Имя</span>
                </div>
                {editName ? (
                  <div className="flex items-center gap-2">
                    <input value={newName} onChange={e => setNewName(e.target.value)} className="text-sm w-32 py-1 px-2" autoFocus />
                    <button onClick={handleSaveName} className="text-xs px-2 py-1 rounded" style={{ color: 'var(--accent)' }}>✓</button>
                  </div>
                ) : (
                  <button onClick={() => setEditName(true)} className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    {currentUser?.displayName}
                  </button>
                )}
              </div>
            </div>

            <div className="p-3 rounded-xl" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <User size={18} style={{ color: 'var(--accent)' }} />
                  <span className="text-sm" style={{ color: 'var(--text-primary)' }}>Username</span>
                </div>
                {editUsername ? (
                  <div className="flex items-center gap-2">
                    <input value={newUsername} onChange={e => setNewUsername(e.target.value)} className="text-sm w-32 py-1 px-2" autoFocus />
                    <button onClick={handleSaveUsername} className="text-xs px-2 py-1 rounded" style={{ color: 'var(--accent)' }}>✓</button>
                  </div>
                ) : (
                  <button onClick={() => setEditUsername(true)} className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    @{currentUser?.username}
                  </button>
                )}
              </div>
            </div>

            <div className="p-3 rounded-xl" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <User size={18} style={{ color: 'var(--accent)' }} />
                  <span className="text-sm" style={{ color: 'var(--text-primary)' }}>О себе</span>
                </div>
                {editBio ? (
                  <div className="flex items-center gap-2">
                    <input value={newBio} onChange={e => setNewBio(e.target.value)} className="text-sm w-40 py-1 px-2" autoFocus />
                    <button onClick={handleSaveBio} className="text-xs px-2 py-1 rounded" style={{ color: 'var(--accent)' }}>✓</button>
                  </div>
                ) : (
                  <button onClick={() => setEditBio(true)} className="text-sm truncate max-w-[200px]" style={{ color: 'var(--text-muted)' }}>
                    {currentUser?.bio || 'Не указано'}
                  </button>
                )}
              </div>
            </div>

            <div className="p-3 rounded-xl cursor-pointer" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
              onClick={() => setEditPassword(!editPassword)}>
              <div className="flex items-center gap-3">
                <Key size={18} style={{ color: 'var(--accent)' }} />
                <span className="text-sm" style={{ color: 'var(--text-primary)' }}>Сменить пароль</span>
              </div>
              {editPassword && (
                <div className="mt-3 space-y-2">
                  <input type="password" placeholder="Текущий пароль" value={oldPass} onChange={e => setOldPass(e.target.value)} className="text-sm" />
                  <input type="password" placeholder="Новый пароль" value={newPass} onChange={e => setNewPass(e.target.value)} className="text-sm" />
                  <button className="btn btn-primary text-sm py-1.5 px-4" onClick={() => { setEditPassword(false); setOldPass(''); setNewPass(''); }}>
                    Сохранить
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="px-4 pb-4">
          <h3 className="text-xs font-semibold uppercase mb-2 px-1" style={{ color: 'var(--text-muted)' }}>Уведомления</h3>
          <div className="rounded-xl overflow-hidden" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
            {[
              { key: 'push' as const, label: 'Push-уведомления', icon: Bell },
              { key: 'sound' as const, label: 'Звук', icon: Bell },
              { key: 'vibration' as const, label: 'Вибрация', icon: Smartphone },
              { key: 'preview' as const, label: 'Показывать текст', icon: Bell },
            ].map(item => (
              <div key={item.key} className="flex items-center justify-between px-3 py-3 border-b last:border-b-0" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-3">
                  <item.icon size={18} style={{ color: 'var(--accent)' }} />
                  <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{item.label}</span>
                </div>
                <button
                  className="w-10 h-6 rounded-full relative transition-colors"
                  style={{ background: settings.notifications[item.key] ? 'var(--accent)' : 'var(--bg-tertiary)' }}
                  onClick={() => updateSettings({ notifications: { ...settings.notifications, [item.key]: !settings.notifications[item.key] } })}
                >
                  <div className="w-4 h-4 rounded-full bg-white absolute top-1 transition-all" style={{ left: settings.notifications[item.key] ? '22px' : '4px' }} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Theme */}
        <div className="px-4 pb-4">
          <h3 className="text-xs font-semibold uppercase mb-2 px-1" style={{ color: 'var(--text-muted)' }}>Внешний вид</h3>
          <div className="rounded-xl overflow-hidden" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
            {[
              { value: 'light' as const, label: '☀️ Светлая' },
              { value: 'dark' as const, label: '🌙 Тёмная' },
              { value: 'system' as const, label: '💻 Системная' },
            ].map(opt => (
              <button
                key={opt.value}
                className="w-full flex items-center gap-3 px-3 py-3 border-b last:border-b-0 text-left"
                style={{ borderColor: 'var(--border)', background: settings.theme === opt.value ? 'rgba(124,92,252,0.1)' : 'transparent' }}
                onClick={() => setTheme(opt.value)}
              >
                <Palette size={18} style={{ color: 'var(--accent)' }} />
                <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{opt.label}</span>
                {settings.theme === opt.value && <span className="ml-auto" style={{ color: 'var(--accent)' }}>✓</span>}
              </button>
            ))}
          </div>
        </div>

        {/* Sessions */}
        <div className="px-4 pb-4">
          <h3 className="text-xs font-semibold uppercase mb-2 px-1" style={{ color: 'var(--text-muted)' }}>Устройства</h3>
          <div className="rounded-xl overflow-hidden" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-3 px-3 py-3 border-b" style={{ borderColor: 'var(--border)' }}>
              <Monitor size={18} style={{ color: 'var(--accent)' }} />
              <div className="flex-1">
                <p className="text-sm" style={{ color: 'var(--text-primary)' }}>Текущее устройство</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Активно сейчас</p>
              </div>
              <span className="w-2 h-2 rounded-full" style={{ background: 'var(--success)' }} />
            </div>
            <button className="w-full text-left px-3 py-3 text-sm" style={{ color: 'var(--danger)' }}
              onClick={() => { if (confirm('Завершить все другие сеансы?')) setSessions([]); }}>
              Завершить все другие сеансы
            </button>
          </div>
        </div>

        {/* Logout */}
        <div className="px-4 pb-8">
          <button className="btn btn-danger w-full" onClick={handleLogout}>
            <LogOut size={18} /> Выйти из аккаунта
          </button>
        </div>
      </div>
    </div>
  );
}
