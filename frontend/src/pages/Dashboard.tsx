import { useEffect, useState } from 'react';
import { api } from '../api/client';

interface SystemStatus {
    telegram: { connected: boolean; user: { first_name: string; username: string } | null };
    channels: { enabled_count: number };
    messages: { total_count: number; last_received_at: string | null };
    database: { size_bytes: number };
    webhooks: { success_count: number; failed_count: number };
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
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

    useEffect(() => {
        api<SystemStatus>('/api/system/status').then(setStatus);
    }, []);

    if (!status) return <p className="text-gray-500">Loading...</p>;

    return (
        <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">System Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <Card title="Telegram">
                    <p className="text-lg font-semibold">
                        {status.telegram.connected ? (
                            <span className="text-green-600">Connected</span>
                        ) : (
                            <span className="text-red-500">Disconnected</span>
                        )}
                    </p>
                    {status.telegram.user && (
                        <p className="text-sm text-gray-600">
                            {status.telegram.user.first_name} (@{status.telegram.user.username})
                        </p>
                    )}
                </Card>

                <Card title="Channels">
                    <p className="text-2xl font-bold text-gray-900">{status.channels.enabled_count}</p>
                    <p className="text-sm text-gray-500">enabled</p>
                </Card>

                <Card title="Messages">
                    <p className="text-2xl font-bold text-gray-900">{status.messages.total_count}</p>
                    <p className="text-sm text-gray-500">
                        {status.messages.last_received_at
                            ? `Last: ${new Date(status.messages.last_received_at).toLocaleString()}`
                            : 'No messages yet'}
                    </p>
                </Card>

                <Card title="Database">
                    <p className="text-2xl font-bold text-gray-900">{formatBytes(status.database.size_bytes)}</p>
                </Card>

                <Card title="Webhooks">
                    <div className="flex gap-4">
                        <div>
                            <p className="text-lg font-bold text-green-600">{status.webhooks.success_count}</p>
                            <p className="text-xs text-gray-500">success</p>
                        </div>
                        <div>
                            <p className="text-lg font-bold text-red-500">{status.webhooks.failed_count}</p>
                            <p className="text-xs text-gray-500">failed</p>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
}
