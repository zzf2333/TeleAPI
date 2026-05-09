import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { CircleCheck, CircleX, ShieldCheck, ShieldAlert } from 'lucide-react';

interface Check {
    name: string;
    ok: boolean;
    count?: number;
}

interface ConfigCheckResponse {
    checks: Check[];
    all_ok: boolean;
}

export default function ConfigCheck() {
    const [data, setData] = useState<ConfigCheckResponse | null>(null);

    useEffect(() => {
        api<ConfigCheckResponse>('/api/system/config-check').then(setData);
    }, []);

    if (!data) return <p className="text-slate-500">加载中...</p>;

    return (
        <div>
            <h2 className="text-xl font-bold text-slate-100 mb-4">配置检查</h2>

            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-700/50 p-5 mb-4">
                <div className="flex items-center gap-2">
                    {data.all_ok
                        ? <ShieldCheck className="w-5 h-5 text-emerald-400" />
                        : <ShieldAlert className="w-5 h-5 text-amber-400" />
                    }
                    <p className={`text-lg font-semibold ${data.all_ok ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {data.all_ok ? '所有检查通过' : '部分检查未通过'}
                    </p>
                </div>
            </div>

            <div className="bg-slate-800/60 backdrop-blur-sm rounded-xl border border-slate-700/50 overflow-hidden">
                <ul className="divide-y divide-slate-700/30">
                    {data.checks.map((check) => (
                        <li key={check.name} className="flex items-center justify-between px-4 py-3 hover:bg-slate-700/20 transition-colors">
                            <span className="text-sm text-slate-300">
                                {check.name}
                                {check.count !== undefined && (
                                    <span className="ml-2 text-slate-500">({check.count})</span>
                                )}
                            </span>
                            {check.ok
                                ? <CircleCheck className="w-5 h-5 text-emerald-400" />
                                : <CircleX className="w-5 h-5 text-rose-400" />
                            }
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}
