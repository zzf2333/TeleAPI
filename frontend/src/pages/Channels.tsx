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

    useEffect(() => {
        api<Channel[]>('/api/channels').then(setChannels);
    }, []);

    return (
        <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">频道</h2>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">用户名</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">标题</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">状态</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-500">消息数</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">最后更新</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {channels.map((ch) => (
                            <tr key={ch.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-mono text-blue-600">@{ch.username}</td>
                                <td className="px-4 py-3">{ch.title}</td>
                                <td className="px-4 py-3">
                                    <span
                                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                                            ch.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                                        }`}
                                    >
                                        {ch.enabled ? '已启用' : '已禁用'}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-right">{ch.message_count}</td>
                                <td className="px-4 py-3 text-gray-500">{new Date(ch.updated_at).toLocaleString()}</td>
                            </tr>
                        ))}
                        {channels.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
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
