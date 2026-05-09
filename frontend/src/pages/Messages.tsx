import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Search, ExternalLink, ChevronDown } from 'lucide-react';

interface Message {
    id: string;
    channel_username: string;
    channel_title: string;
    type: string;
    text: string | null;
    date: string;
    url: string;
}

interface Channel {
    id: string;
    username: string;
}

interface MessagesResponse {
    data: Message[];
    next_cursor: string | null;
}

export default function Messages() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [channels, setChannels] = useState<Channel[]>([]);
    const [selectedChannel, setSelectedChannel] = useState('');
    const [keyword, setKeyword] = useState('');
    const [nextCursor, setNextCursor] = useState<string | null>(null);

    useEffect(() => {
        api<Channel[]>('/api/channels').then(setChannels);
    }, []);

    useEffect(() => {
        loadMessages();
    }, [selectedChannel]);

    async function loadMessages(cursor?: string) {
        if (!selectedChannel && channels.length === 0) return;
        const channelId = selectedChannel || (channels[0]?.id ?? '');
        if (!channelId) return;

        let url = `/api/channels/${channelId}/messages?limit=50`;
        if (cursor) url += `&cursor=${cursor}`;
        if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;

        const data = await api<MessagesResponse>(url);
        if (cursor) {
            setMessages((prev) => [...prev, ...data.data]);
        } else {
            setMessages(data.data);
        }
        setNextCursor(data.next_cursor);
    }

    function handleSearch(e: React.FormEvent) {
        e.preventDefault();
        setNextCursor(null);
        loadMessages();
    }

    const inputClass = 'px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-colors';

    return (
        <div>
            <h2 className="text-xl font-bold text-slate-100 mb-4">消息</h2>

            <form onSubmit={handleSearch} className="flex gap-3 mb-4">
                <select
                    value={selectedChannel}
                    onChange={(e) => setSelectedChannel(e.target.value)}
                    className={inputClass}
                >
                    <option value="">全部频道</option>
                    {channels.map((ch) => (
                        <option key={ch.id} value={ch.id}>
                            @{ch.username}
                        </option>
                    ))}
                </select>
                <div className="flex-1 relative">
                    <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                        type="text"
                        value={keyword}
                        onChange={(e) => setKeyword(e.target.value)}
                        placeholder="搜索关键词..."
                        className={`w-full pl-9 ${inputClass}`}
                    />
                </div>
                <button type="submit" className="px-4 py-2 bg-cyan-600 text-white rounded-lg text-sm hover:bg-cyan-500 transition-colors">
                    搜索
                </button>
            </form>

            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-slate-700/40 border-b border-slate-700/50">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">时间</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">频道</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">类型</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">内容</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">链接</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/30">
                        {messages.map((m) => (
                            <tr key={m.id} className="hover:bg-slate-700/20">
                                <td className="px-4 py-3 text-slate-500 whitespace-nowrap">{new Date(m.date).toLocaleString()}</td>
                                <td className="px-4 py-3 font-mono text-xs text-cyan-400">@{m.channel_username}</td>
                                <td className="px-4 py-3">
                                    <span className="px-2 py-0.5 rounded-md bg-slate-700/40 text-xs text-slate-400">{m.type}</span>
                                </td>
                                <td className="px-4 py-3 max-w-md truncate text-slate-300">{m.text || '-'}</td>
                                <td className="px-4 py-3">
                                    <a href={m.url} target="_blank" rel="noreferrer" className="text-cyan-400 hover:text-cyan-300 transition-colors inline-flex items-center gap-1">
                                        <ExternalLink className="w-3.5 h-3.5" />
                                    </a>
                                </td>
                            </tr>
                        ))}
                        {messages.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                                    暂无消息
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {nextCursor && (
                <button
                    onClick={() => loadMessages(nextCursor)}
                    className="mt-4 px-4 py-2 border border-slate-600 rounded-lg text-sm text-slate-400 hover:bg-slate-700/40 hover:text-slate-200 transition-colors flex items-center gap-1.5"
                >
                    <ChevronDown className="w-4 h-4" />
                    加载更多
                </button>
            )}
        </div>
    );
}
