import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Zap, ZapOff, Radio, MessageSquareText, Database, Webhook, Link } from 'lucide-react';

interface SystemStatus {
    telegram: { connected: boolean; user: { first_name: string; username: string } | null };
    channels: { enabled_count: number };
    messages: { total_count: number; last_received_at: string | null };
    database: { size_bytes: number };
    webhooks: { success_count: number; failed_count: number };
}

function Card({ title, icon: Icon, iconColor, children }: {
    title: string;
    icon: React.ComponentType<{ className?: string }>;
    iconColor: string;
    children: React.ReactNode;
}) {
    return (
        <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-700/50 p-5 hover:border-slate-600/50 transition-colors">
            <div className="flex items-center gap-2 mb-3">
                <Icon className={`w-4 h-4 ${iconColor}`} />
                <h3 className="text-sm font-medium text-slate-400">{title}</h3>
            </div>
            {children}
        </div>
    );
}

function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function Dashboard() {
    const [status, setStatus] = useState<SystemStatus | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        api<SystemStatus>('/api/system/status').then(setStatus);
    }, []);

    if (!status) return <p className="text-slate-500">加载中...</p>;

    return (
        <div>
            <h2 className="text-xl font-bold text-slate-100 mb-4">系统状态</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <Card
                    title="Telegram"
                    icon={status.telegram.connected ? Zap : ZapOff}
                    iconColor={status.telegram.connected ? 'text-emerald-400' : 'text-rose-400'}
                >
                    <p className="text-lg font-semibold">
                        {status.telegram.connected ? (
                            <span className="text-emerald-400">已连接</span>
                        ) : (
                            <span className="text-rose-400">未连接</span>
                        )}
                    </p>
                    {status.telegram.user && (
                        <p className="text-sm text-slate-400">
                            {status.telegram.user.first_name}
                            {status.telegram.user.username && ` (@${status.telegram.user.username})`}
                        </p>
                    )}
                    {!status.telegram.connected && (
                        <button
                            onClick={() => navigate('/login', { state: { skipKey: true } })}
                            className="mt-2 px-3 py-1.5 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 transition-colors flex items-center gap-1.5"
                        >
                            <Link className="w-3.5 h-3.5" />
                            连接 Telegram
                        </button>
                    )}
                </Card>

                <Card title="频道" icon={Radio} iconColor="text-violet-400">
                    <p className="text-2xl font-bold text-slate-100">{status.channels.enabled_count}</p>
                    <p className="text-sm text-slate-500">已启用</p>
                </Card>

                <Card title="消息" icon={MessageSquareText} iconColor="text-cyan-400">
                    <p className="text-2xl font-bold text-slate-100">{status.messages.total_count}</p>
                    <p className="text-sm text-slate-500">
                        {status.messages.last_received_at
                            ? `最近: ${new Date(status.messages.last_received_at).toLocaleString()}`
                            : '暂无消息'}
                    </p>
                </Card>

                <Card title="数据库" icon={Database} iconColor="text-sky-400">
                    <p className="text-2xl font-bold text-slate-100">{formatBytes(status.database.size_bytes)}</p>
                </Card>

                <Card title="Webhook" icon={Webhook} iconColor="text-amber-400">
                    <div className="flex gap-4">
                        <div>
                            <p className="text-lg font-bold text-emerald-400">{status.webhooks.success_count}</p>
                            <p className="text-xs text-slate-500">成功</p>
                        </div>
                        <div>
                            <p className="text-lg font-bold text-rose-400">{status.webhooks.failed_count}</p>
                            <p className="text-xs text-slate-500">失败</p>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
}
