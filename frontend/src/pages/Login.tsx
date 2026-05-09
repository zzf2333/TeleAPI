import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { setApiKey, getApiKey, api } from '../api/client';

export default function Login() {
    const location = useLocation();
    const skipKey = !!(location.state as { skipKey?: boolean })?.skipKey && !!getApiKey();

    const [key, setKey] = useState('');
    const [error, setError] = useState('');
    const [authed, setAuthed] = useState(skipKey);
    const navigate = useNavigate();

    const [loginMethod, setLoginMethod] = useState<'qr' | 'phone'>('qr');

    const [qrImage, setQrImage] = useState('');
    const [qrStatus, setQrStatus] = useState('');

    const [phone, setPhone] = useState('');
    const [verificationCode, setVerificationCode] = useState('');
    const [phoneStatus, setPhoneStatus] = useState('');

    const [password, setPassword] = useState('');

    async function handleKeySubmit(e: React.FormEvent) {
        e.preventDefault();
        setApiKey(key);
        try {
            await api('/api/auth/status');
            setAuthed(true);
            setError('');
        } catch {
            setError('密钥无效');
        }
    }

    async function startQrLogin() {
        try {
            const data = await api<{ status: string; qr_image: string }>('/api/auth/qr-login', { method: 'POST' });
            setQrImage(data.qr_image);
            setQrStatus(data.status);
            pollStatus();
        } catch (e: unknown) {
            setError(String(e));
        }
    }

    async function pollStatus() {
        const interval = setInterval(async () => {
            try {
                const data = await api<{ status: string }>('/api/auth/qr-login/status');
                setQrStatus(data.status);
                if (data.status === 'success') {
                    clearInterval(interval);
                    navigate('/');
                } else if (data.status === '2fa_required' || data.status === 'expired' || data.status === 'error') {
                    clearInterval(interval);
                }
            } catch {
                clearInterval(interval);
            }
        }, 2000);
    }

    async function refreshQr() {
        try {
            const data = await api<{ status: string; qr_image: string }>('/api/auth/qr-login/refresh', { method: 'POST' });
            setQrImage(data.qr_image);
            setQrStatus(data.status);
            pollStatus();
        } catch (e: unknown) {
            setError(String(e));
        }
    }

    async function sendCode() {
        setError('');
        try {
            const data = await api<{ status: string; error?: string }>('/api/auth/phone-login/send-code', {
                method: 'POST',
                body: JSON.stringify({ phone }),
            });
            setPhoneStatus(data.status);
            if (data.error) setError(data.error);
        } catch (e: unknown) {
            setError(String(e));
        }
    }

    async function verifyCode(e: React.FormEvent) {
        e.preventDefault();
        setError('');
        try {
            const data = await api<{ status: string; error?: string }>('/api/auth/phone-login/verify-code', {
                method: 'POST',
                body: JSON.stringify({ code: verificationCode }),
            });
            setPhoneStatus(data.status);
            if (data.status === 'success') {
                navigate('/');
            } else if (data.error) {
                setError(data.error);
            }
        } catch (e: unknown) {
            setError(String(e));
        }
    }

    async function handle2fa(e: React.FormEvent) {
        e.preventDefault();
        try {
            const data = await api<{ status: string; error?: string }>('/api/auth/2fa', {
                method: 'POST',
                body: JSON.stringify({ password }),
            });
            if (data.status === 'success') {
                navigate('/');
            } else {
                setError(data.error || '两步验证失败');
            }
        } catch (e: unknown) {
            setError(String(e));
        }
    }

    const show2fa = qrStatus === '2fa_required' || phoneStatus === '2fa_required';

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
                <h1 className="text-2xl font-bold text-gray-900 mb-6">TeleAPI</h1>

                {!authed ? (
                    <form onSubmit={handleKeySubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">管理密钥</label>
                            <input
                                type="password"
                                value={key}
                                onChange={(e) => setKey(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="请输入管理密钥"
                            />
                        </div>
                        {error && <p className="text-red-500 text-sm">{error}</p>}
                        <button
                            type="submit"
                            className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            验证
                        </button>
                    </form>
                ) : (
                    <div className="space-y-4">
                        <p className="text-green-600 text-sm">密钥验证通过</p>

                        {!show2fa && (
                            <>
                                <div className="flex border-b border-gray-200 mb-4">
                                    <button
                                        onClick={() => { setLoginMethod('qr'); setError(''); }}
                                        className={`flex-1 py-2 text-sm font-medium border-b-2 transition-colors ${
                                            loginMethod === 'qr'
                                                ? 'border-blue-600 text-blue-600'
                                                : 'border-transparent text-gray-500 hover:text-gray-700'
                                        }`}
                                    >
                                        扫码登录
                                    </button>
                                    <button
                                        onClick={() => { setLoginMethod('phone'); setError(''); }}
                                        className={`flex-1 py-2 text-sm font-medium border-b-2 transition-colors ${
                                            loginMethod === 'phone'
                                                ? 'border-blue-600 text-blue-600'
                                                : 'border-transparent text-gray-500 hover:text-gray-700'
                                        }`}
                                    >
                                        手机号登录
                                    </button>
                                </div>

                                {loginMethod === 'qr' && (
                                    <>
                                        {!qrImage && qrStatus !== '2fa_required' && (
                                            <div className="space-y-3">
                                                <button
                                                    onClick={startQrLogin}
                                                    className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                                >
                                                    生成二维码
                                                </button>
                                            </div>
                                        )}

                                        {qrImage && qrStatus === 'waiting' && (
                                            <div className="text-center space-y-3">
                                                <p className="text-sm text-gray-600">请使用 Telegram 手机客户端扫码</p>
                                                <img src={qrImage} alt="QR Code" className="mx-auto w-48 h-48" />
                                                <p className="text-xs text-gray-400">等待扫码...</p>
                                            </div>
                                        )}

                                        {qrStatus === 'expired' && (
                                            <div className="text-center space-y-3">
                                                <p className="text-sm text-amber-600">二维码已过期</p>
                                                <button onClick={refreshQr} className="py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700">
                                                    重新生成
                                                </button>
                                            </div>
                                        )}
                                    </>
                                )}

                                {loginMethod === 'phone' && (
                                    <>
                                        {(!phoneStatus || phoneStatus === 'idle') && (
                                            <div className="space-y-3">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">手机号</label>
                                                    <input
                                                        type="tel"
                                                        value={phone}
                                                        onChange={(e) => setPhone(e.target.value)}
                                                        className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                        placeholder="+8613800138000"
                                                    />
                                                    <p className="text-xs text-gray-400 mt-1">请使用国际格式，以 + 开头</p>
                                                </div>
                                                <button
                                                    onClick={sendCode}
                                                    className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                                >
                                                    发送验证码
                                                </button>
                                            </div>
                                        )}

                                        {phoneStatus === 'code_sent' && (
                                            <form onSubmit={verifyCode} className="space-y-3">
                                                <p className="text-sm text-green-600">验证码已发送至 {phone}</p>
                                                <input
                                                    type="text"
                                                    value={verificationCode}
                                                    onChange={(e) => setVerificationCode(e.target.value)}
                                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                    placeholder="请输入验证码"
                                                    autoFocus
                                                />
                                                <button type="submit" className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                                                    验证
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={sendCode}
                                                    className="w-full py-1 text-sm text-blue-600 hover:text-blue-800"
                                                >
                                                    重新发送
                                                </button>
                                            </form>
                                        )}

                                        {phoneStatus === 'expired' && (
                                            <div className="text-center space-y-3">
                                                <p className="text-sm text-amber-600">验证码已过期</p>
                                                <button onClick={sendCode} className="py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700">
                                                    重新发送
                                                </button>
                                            </div>
                                        )}

                                        {phoneStatus === 'error' && (
                                            <div className="space-y-3">
                                                <button
                                                    onClick={() => { setPhoneStatus(''); setError(''); }}
                                                    className="w-full py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
                                                >
                                                    重试
                                                </button>
                                            </div>
                                        )}
                                    </>
                                )}

                                <button
                                    onClick={() => navigate('/')}
                                    className="w-full py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
                                >
                                    跳过（已登录）
                                </button>
                            </>
                        )}

                        {show2fa && (
                            <form onSubmit={handle2fa} className="space-y-3">
                                <p className="text-sm text-amber-600">需要两步验证密码</p>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="请输入两步验证密码"
                                />
                                <button type="submit" className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                                    提交
                                </button>
                            </form>
                        )}

                        {error && <p className="text-red-500 text-sm">{error}</p>}
                    </div>
                )}
            </div>
        </div>
    );
}
