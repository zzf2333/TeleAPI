import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { clearApiKey } from '../api/client';
import { LayoutDashboard, Radio, MessageSquareText, RefreshCw, Webhook, Settings, LogOut, Zap } from 'lucide-react';

const navItems = [
    { to: '/', label: '仪表盘', icon: LayoutDashboard },
    { to: '/channels', label: '频道', icon: Radio },
    { to: '/messages', label: '消息', icon: MessageSquareText },
    { to: '/sync-jobs', label: '同步任务', icon: RefreshCw },
    { to: '/webhook-logs', label: 'Webhook 日志', icon: Webhook },
    { to: '/config-check', label: '配置检查', icon: Settings },
];

export default function Layout() {
    const navigate = useNavigate();

    function handleLogout() {
        clearApiKey();
        navigate('/login');
    }

    return (
        <div className="flex h-screen bg-slate-950">
            <aside className="w-56 bg-slate-900 border-r border-slate-700/50 flex flex-col">
                <div className="p-4 border-b border-slate-700/50">
                    <h1 className="text-lg font-bold text-cyan-400 tracking-wide flex items-center gap-1.5">
                        <Zap className="w-4 h-4" />
                        TeleAPI
                    </h1>
                    <p className="text-xs text-slate-500">管理面板</p>
                </div>
                <nav className="flex-1 p-2 space-y-1">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.to === '/'}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                                    isActive
                                        ? 'bg-cyan-500/10 text-cyan-400 font-medium shadow-[inset_2px_0_0_theme(--color-cyan-400)]'
                                        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                                }`
                            }
                        >
                            <item.icon className="w-4 h-4 shrink-0" />
                            {item.label}
                        </NavLink>
                    ))}
                </nav>
                <div className="p-2 border-t border-slate-700/50">
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-3 py-2 text-sm text-slate-400 hover:text-rose-400 hover:bg-rose-400/10 rounded-lg text-left transition-colors"
                    >
                        <LogOut className="w-4 h-4" />
                        退出登录
                    </button>
                </div>
            </aside>
            <main className="flex-1 overflow-auto p-6 bg-slate-950">
                <Outlet />
            </main>
        </div>
    );
}
