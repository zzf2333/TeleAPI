import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Plus, X, Trash2 } from 'lucide-react';

interface Channel {
    id: string;
    telegram_id: number;
    username: string;
    title: string;
    enabled: boolean;
    message_count: number;
    updated_at: string;
}

export default function Channels() {
    const [channels, setChannels] = useState<Channel[]>([]);
    const [showAdd, setShowAdd] = useState(false);
    const [username, setUsername] = useState('');
    const [syncHistory, setSyncHistory] = useState(false);
    const [historyLimit, setHistoryLimit] = useState(100);
    const [adding, setAdding] = useState(false);
    const [error, setError] = useState('');
    const [busyId, setBusyId] = useState('');

    const loadChannels = () => api<Channel[]>('/api/channels').then(setChannels);

    useEffect(() => { loadChannels(); }, []);

    async function handleAdd(e: React.FormEvent) {
        e.preventDefault();
        setError('');
        setAdding(true);
        try {
            await api('/api/channels', {
                method: 'POST',
                body: JSON.stringify({
                    username: username.replace(/^@/, ''),
                    sync_history: syncHistory,
                    history_limit: historyLimit,
                }),
            });
            setUsername('');
            setSyncHistory(false);
            setHistoryLimit(100);
            setShowAdd(false);
            await loadChannels();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : '添加失败');
        } finally {
            setAdding(false);
        }
    }

    async function handleToggle(ch: Channel) {
        setBusyId(ch.id);
        try {
            await api(`/api/channels/${ch.id}`, {
                method: 'PUT',
                body: JSON.stringify({ enabled: !ch.enabled }),
            });
            await loadChannels();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : '操作失败');
        } finally {
            setBusyId('');
        }
    }

    async function handleDelete(ch: Channel) {
        if (!confirm(`确定删除频道 @${ch.username}？关联的消息和同步记录将一并删除。`)) return;
        setBusyId(ch.id);
        try {
            await api(`/api/channels/${ch.id}`, { method: 'DELETE' });
            await loadChannels();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : '删除失败');
        } finally {
            setBusyId('');
        }
    }

    const inputClass = 'px-3 py-1.5 text-sm bg-slate-800 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-colors';

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-slate-100">频道</h2>
                <button
                    onClick={() => { setShowAdd(!showAdd); setError(''); }}
                    className="px-3 py-1.5 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 transition-colors flex items-center gap-1.5"
                >
                    {showAdd ? <><X className="w-3.5 h-3.5" />取消</> : <><Plus className="w-3.5 h-3.5" />添加频道</>}
                </button>
            </div>

            {error && (
                <div className="mb-4 p-3 bg-rose-400/15 border border-rose-400/30 rounded-xl text-sm text-rose-400 flex items-center justify-between">
                    <span>{error}</span>
                    <button onClick={() => setError('')} className="text-rose-400/60 hover:text-rose-400 ml-2">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            {showAdd && (
                <form onSubmit={handleAdd} className="mb-4 p-4 bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-700/50">
                    <div className="flex items-end gap-3 flex-wrap">
                        <div className="flex-1 min-w-48">
                            <label className="block text-xs font-medium text-slate-400 mb-1">频道用户名</label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="channel_username"
                                required
                                className={`w-full ${inputClass}`}
                            />
                        </div>
                        <label className="flex items-center gap-1.5 text-sm text-slate-300 pb-0.5">
                            <input
                                type="checkbox"
                                checked={syncHistory}
                                onChange={(e) => setSyncHistory(e.target.checked)}
                                className="rounded accent-cyan-500"
                            />
                            同步历史
                        </label>
                        {syncHistory && (
                            <div>
                                <label className="block text-xs font-medium text-slate-400 mb-1">消息数量</label>
                                <input
                                    type="number"
                                    value={historyLimit}
                                    onChange={(e) => setHistoryLimit(Number(e.target.value))}
                                    min={1}
                                    max={10000}
                                    className={`w-24 ${inputClass}`}
                                />
                            </div>
                        )}
                        <button
                            type="submit"
                            disabled={adding || !username.trim()}
                            className="px-4 py-1.5 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 disabled:opacity-50 transition-colors"
                        >
                            {adding ? '添加中...' : '添加'}
                        </button>
                    </div>
                </form>
            )}

            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-slate-700/40 border-b border-slate-700/50">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">频道 ID</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">用户名</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">标题</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">状态</th>
                            <th className="text-right px-4 py-3 font-medium text-slate-400">消息数</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">最后更新</th>
                            <th className="text-right px-4 py-3 font-medium text-slate-400">操作</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/30">
                        {channels.map((ch) => (
                            <tr key={ch.id} className="hover:bg-slate-700/20">
                                <td className="px-4 py-3 font-mono text-xs text-slate-500">{ch.telegram_id}</td>
                                <td className="px-4 py-3 font-mono text-cyan-400">@{ch.username}</td>
                                <td className="px-4 py-3 text-slate-300">{ch.title}</td>
                                <td className="px-4 py-3">
                                    <button
                                        onClick={() => handleToggle(ch)}
                                        disabled={busyId === ch.id}
                                        className={`px-2 py-0.5 rounded-md text-xs font-medium cursor-pointer disabled:opacity-50 border transition-colors ${
                                            ch.enabled
                                                ? 'bg-emerald-400/15 text-emerald-400 border-emerald-400/30 hover:bg-emerald-400/25'
                                                : 'bg-slate-700/40 text-slate-500 border-slate-600/30 hover:bg-slate-700/60'
                                        }`}
                                    >
                                        {ch.enabled ? '已启用' : '已禁用'}
                                    </button>
                                </td>
                                <td className="px-4 py-3 text-right text-slate-300">{ch.message_count}</td>
                                <td className="px-4 py-3 text-slate-500">{new Date(ch.updated_at).toLocaleString()}</td>
                                <td className="px-4 py-3 text-right">
                                    <button
                                        onClick={() => handleDelete(ch)}
                                        disabled={busyId === ch.id}
                                        className="text-rose-400/60 hover:text-rose-400 disabled:opacity-50 transition-colors"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {channels.length === 0 && (
                            <tr>
                                <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                                    暂无频道
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
