import { useEffect, useState } from 'react';
import { api } from '../api/client';

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

    if (!data) return <p className="text-gray-500">加载中...</p>;

    return (
        <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">配置检查</h2>

            <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
                <p className={`text-lg font-semibold ${data.all_ok ? 'text-green-600' : 'text-amber-600'}`}>
                    {data.all_ok ? '所有检查通过' : '部分检查未通过'}
                </p>
            </div>

            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <ul className="divide-y divide-gray-100">
                    {data.checks.map((check) => (
                        <li key={check.name} className="flex items-center justify-between px-4 py-3">
                            <span className="text-sm text-gray-700">
                                {check.name}
                                {check.count !== undefined && (
                                    <span className="ml-2 text-gray-400">({check.count})</span>
                                )}
                            </span>
                            <span className={`text-lg ${check.ok ? 'text-green-500' : 'text-red-500'}`}>
                                {check.ok ? '✓' : '✗'}
                            </span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}
