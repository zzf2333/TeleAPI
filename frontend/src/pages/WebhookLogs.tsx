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
            <h2 className="text-xl font-bold text-gray-900 mb-4">Webhook Delivery Logs</h2>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Webhook</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Event</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-500">HTTP Code</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-500">Attempts</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Error</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Time</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {deliveries.map((d) => (
                            <tr key={d.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3">{d.webhook_name}</td>
                                <td className="px-4 py-3 text-xs">{d.event}</td>
                                <td className="px-4 py-3">
                                    <span
                                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                                            d.status === 'success'
                                                ? 'bg-green-100 text-green-700'
                                                : 'bg-red-100 text-red-700'
                                        }`}
                                    >
                                        {d.status}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-right">{d.response_status ?? '-'}</td>
                                <td className="px-4 py-3 text-right">{d.attempts}</td>
                                <td className="px-4 py-3 text-red-500 text-xs max-w-xs truncate">{d.error || '-'}</td>
                                <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{new Date(d.created_at).toLocaleString()}</td>
                            </tr>
                        ))}
                        {deliveries.length === 0 && (
                            <tr>
                                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                                    No webhook deliveries
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
