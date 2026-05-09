import { useEffect, useState } from 'react';
import { api } from '../api/client';

interface Delivery {
    id: string;
    webhook_name: string;
    event: string;
    status: string;
    attempts: number;
    response_status: number | null;
    error: string | null;
    created_at: string;
}

export default function WebhookLogs() {
    const [deliveries, setDeliveries] = useState<Delivery[]>([]);

    useEffect(() => {
        api<Delivery[]>('/api/webhook-deliveries?limit=50').then(setDeliveries);
    }, []);

    return (
        <div>
            <h2 className="text-xl font-bold text-slate-100 mb-4">Webhook 推送日志</h2>
            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-slate-700/40 border-b border-slate-700/50">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">Webhook</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">事件</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">状态</th>
                            <th className="text-right px-4 py-3 font-medium text-slate-400">HTTP 状态码</th>
                            <th className="text-right px-4 py-3 font-medium text-slate-400">重试次数</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">错误</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">时间</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/30">
                        {deliveries.map((d) => (
                            <tr key={d.id} className="hover:bg-slate-700/20">
                                <td className="px-4 py-3 text-slate-300">{d.webhook_name}</td>
                                <td className="px-4 py-3 text-xs text-slate-400">{d.event}</td>
                                <td className="px-4 py-3">
                                    <span
                                        className={`px-2 py-0.5 rounded-md text-xs font-medium border ${
                                            d.status === 'success'
                                                ? 'bg-emerald-400/15 text-emerald-400 border-emerald-400/30'
                                                : 'bg-rose-400/15 text-rose-400 border-rose-400/30'
                                        }`}
                                    >
                                        {d.status}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-right text-slate-300">{d.response_status ?? '-'}</td>
                                <td className="px-4 py-3 text-right text-slate-300">{d.attempts}</td>
                                <td className="px-4 py-3 text-rose-400 text-xs max-w-xs truncate">{d.error || '-'}</td>
                                <td className="px-4 py-3 text-slate-500 whitespace-nowrap">{new Date(d.created_at).toLocaleString()}</td>
                            </tr>
                        ))}
                        {deliveries.length === 0 && (
                            <tr>
                                <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                                    暂无推送记录
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
