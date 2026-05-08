import { useEffect, useState } from 'react';
import { api } from '../api/client';

interface SyncJob {
    id: string;
    channel_id: string;
    status: string;
    total: number | null;
    synced: number;
    error: string | null;
    started_at: string | null;
    finished_at: string | null;
    created_at: string;
}

const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    running: 'bg-blue-100 text-blue-700',
    success: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
};

export default function SyncJobs() {
    const [jobs, setJobs] = useState<SyncJob[]>([]);

    useEffect(() => {
        api<SyncJob[]>('/api/sync-jobs?limit=50').then(setJobs);
    }, []);

    return (
        <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Sync Jobs</h2>
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Job ID</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                            <th className="text-right px-4 py-3 font-medium text-gray-500">Progress</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Error</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Started</th>
                            <th className="text-left px-4 py-3 font-medium text-gray-500">Finished</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {jobs.map((j) => (
                            <tr key={j.id} className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-mono text-xs">{j.id.slice(0, 8)}</td>
                                <td className="px-4 py-3">
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColors[j.status] || 'bg-gray-100'}`}>
                                        {j.status}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-right">
                                    {j.synced}{j.total ? ` / ${j.total}` : ''}
                                </td>
                                <td className="px-4 py-3 text-red-500 text-xs max-w-xs truncate">{j.error || '-'}</td>
                                <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                                    {j.started_at ? new Date(j.started_at).toLocaleString() : '-'}
                                </td>
                                <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                                    {j.finished_at ? new Date(j.finished_at).toLocaleString() : '-'}
                                </td>
                            </tr>
                        ))}
                        {jobs.length === 0 && (
                            <tr>
                                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                                    No sync jobs
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
