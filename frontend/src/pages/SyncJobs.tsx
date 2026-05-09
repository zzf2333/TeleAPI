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
    pending: 'bg-amber-400/15 text-amber-400 border-amber-400/30',
    running: 'bg-cyan-400/15 text-cyan-400 border-cyan-400/30',
    success: 'bg-emerald-400/15 text-emerald-400 border-emerald-400/30',
    failed: 'bg-rose-400/15 text-rose-400 border-rose-400/30',
};

export default function SyncJobs() {
    const [jobs, setJobs] = useState<SyncJob[]>([]);

    useEffect(() => {
        api<SyncJob[]>('/api/sync-jobs?limit=50').then(setJobs);
    }, []);

    return (
        <div>
            <h2 className="text-xl font-bold text-slate-100 mb-4">同步任务</h2>
            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-slate-700/40 border-b border-slate-700/50">
                        <tr>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">任务 ID</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">状态</th>
                            <th className="text-right px-4 py-3 font-medium text-slate-400">进度</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">错误</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">开始时间</th>
                            <th className="text-left px-4 py-3 font-medium text-slate-400">完成时间</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/30">
                        {jobs.map((j) => (
                            <tr key={j.id} className="hover:bg-slate-700/20">
                                <td className="px-4 py-3 font-mono text-xs text-slate-500">{j.id.slice(0, 8)}</td>
                                <td className="px-4 py-3">
                                    <span className={`px-2 py-0.5 rounded-md text-xs font-medium border ${statusColors[j.status] || 'bg-slate-700/40 text-slate-400 border-slate-600/30'}`}>
                                        {j.status}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-right text-slate-300">
                                    {j.synced}{j.total ? ` / ${j.total}` : ''}
                                </td>
                                <td className="px-4 py-3 text-rose-400 text-xs max-w-xs truncate">{j.error || '-'}</td>
                                <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                                    {j.started_at ? new Date(j.started_at).toLocaleString() : '-'}
                                </td>
                                <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                                    {j.finished_at ? new Date(j.finished_at).toLocaleString() : '-'}
                                </td>
                            </tr>
                        ))}
                        {jobs.length === 0 && (
                            <tr>
                                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                                    暂无同步任务
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
