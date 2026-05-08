import { useEffect, useState } from 'react';
import { api } from '../api/client';

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

    return (
        <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">消息</h2>

            <form onSubmit={handleSearch} className="flex gap-3 mb-4">
                <select
                    value={selectedChannel}
                    onChange={(e) => setSelectedChannel(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded text-sm"
                >
                    <option value="">全部频道</option>
                    {channels.map((ch) => (
                        <option key={ch.id} value={ch.id}>
                            @{ch.username}
                        </option>
                    ))}
                </select>
                <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="搜索关键词..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
                />
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
                    搜索
                </button>
            </form>

            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">时间</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">频道</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">类型</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">内容</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">链接</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {messages.map((m) => (
                            <tr key={m.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{new Date(m.date).toLocaleString()}</td>
                                <td className="px-4 py-3 font-mono text-xs">@{m.channel_username}</td>
                                <td className="px-4 py-3">
                                    <span className="px-2 py-0.5 rounded bg-gray-100 text-xs">{m.type}</span>
                                </td>
                                <td className="px-4 py-3 max-w-md truncate">{m.text || '-'}</td>
                                <td className="px-4 py-3">
                                    <a href={m.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs">
                                        打开
                                    </a>
                                </td>
                            </tr>
                        ))}
                        {messages.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
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
                    className="mt-4 px-4 py-2 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-50"
                >
                    加载更多
                </button>
            )}
        </div>
    );
}
