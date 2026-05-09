import { useEffect, useState } from 'react';
import { api } from '../api/client';

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

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">频道</h2>
                <button
                    onClick={() => { setShowAdd(!showAdd); setError(''); }}
                    className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                    {showAdd ? '取消' : '添加频道'}
                </button>
            </div>

            {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700 flex items-center justify-between">
                    <span>{error}</span>
                    <button onClick={() => setError('')} className="text-red-400 hover:text-red-600 ml-2">✕</button>
                </div>
            )}

            {showAdd && (
                <form onSubmit={handleAdd} className="mb-4 p-4 bg-white rounded-lg border border-gray-200">
                    <div className="flex items-end gap-3 flex-wrap">
                        <div className="flex-1 min-w-48">
                            <label className="block text-xs font-medium text-gray-500 mb-1">频道用户名</label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="channel_username"
                                required
                                className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <label className="flex items-center gap-1.5 text-sm text-gray-700 pb-0.5">
                            <input
                                type="checkbox"
                                checked={syncHistory}
                                onChange={(e) => setSyncHistory(e.target.checked)}
                                className="rounded"
                            />
                            同步历史
                        </label>
                        {syncHistory && (
                            <div>
                                <label className="block text-xs font-medium text-gray-500 mb-1">消息数量</label>
                                <input
                                    type="number"
                                    value={historyLimit}
                                    onChange={(e) => setHistoryLimit(Number(e.target.value))}
                                    min={1}
                                    max={10000}
                                    className="w-24 px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        )}
                        <button
                            type="submit"
                            disabled={adding || !username.trim()}
                            className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                            {adding ? '添加中...' : '添加'}
                        </button>
                    </div>
                </form>
            )}

            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">频道 ID</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">用户名</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">标题</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">状态</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-500">消息数</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">最后更新</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-500">操作</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {channels.map((ch) => (
                            <tr key={ch.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-mono text-xs text-gray-500">{ch.telegram_id}</td>
                                <td className="px-4 py-3 font-mono text-blue-600">@{ch.username}</td>
                                <td className="px-4 py-3">{ch.title}</td>
                                <td className="px-4 py-3">
                                    <button
                                        onClick={() => handleToggle(ch)}
                                        disabled={busyId === ch.id}
                                        className={`px-2 py-0.5 rounded text-xs font-medium cursor-pointer disabled:opacity-50 ${
                                            ch.enabled
                                                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                                                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                                        }`}
                                    >
                                        {ch.enabled ? '已启用' : '已禁用'}
                                    </button>
                                </td>
                                <td className="px-4 py-3 text-right">{ch.message_count}</td>
                                <td className="px-4 py-3 text-gray-500">{new Date(ch.updated_at).toLocaleString()}</td>
                                <td className="px-4 py-3 text-right">
                                    <button
                                        onClick={() => handleDelete(ch)}
                                        disabled={busyId === ch.id}
                                        className="text-red-500 hover:text-red-700 text-sm disabled:opacity-50"
                                    >
                                        删除
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {channels.length === 0 && (
                            <tr>
                                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
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
