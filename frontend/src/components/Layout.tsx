import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { clearApiKey } from '../api/client';

const navItems = [
    { to: '/', label: '仪表盘' },
    { to: '/channels', label: '频道' },
    { to: '/messages', label: '消息' },
    { to: '/sync-jobs', label: '同步任务' },
    { to: '/webhook-logs', label: 'Webhook 日志' },
    { to: '/config-check', label: '配置检查' },
];

export default function Layout() {
    const navigate = useNavigate();

    function handleLogout() {
        clearApiKey();
        navigate('/login');
    }

    return (
        <div className="flex h-screen bg-gray-50">
            <aside className="w-56 bg-white border-r border-gray-200 flex flex-col">
                <div className="p-4 border-b border-gray-200">
                    <h1 className="text-lg font-bold text-gray-900">TeleAPI</h1>
                    <p className="text-xs text-gray-500">管理面板</p>
                </div>
                <nav className="flex-1 p-2 space-y-1">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.to === '/'}
                            className={({ isActive }) =>
                                `block px-3 py-2 rounded text-sm ${
                                    isActive
                                        ? 'bg-blue-50 text-blue-700 font-medium'
                                        : 'text-gray-700 hover:bg-gray-100'
                                }`
                            }
                        >
                            {item.label}
                        </NavLink>
                    ))}
                </nav>
                <div className="p-2 border-t border-gray-200">
                    <button
                        onClick={handleLogout}
                        className="w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded text-left"
                    >
                        退出登录
                    </button>
                </div>
            </aside>
            <main className="flex-1 overflow-auto p-6">
                <Outlet />
            </main>
        </div>
    );
}
