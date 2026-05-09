import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { setApiKey, getApiKey, api } from '../api/client';
import { KeyRound, QrCode, Smartphone, ShieldCheck } from 'lucide-react';

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

    const inputClass = 'w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-colors';
    const primaryBtn = 'w-full py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 transition-colors';

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950">
            <div className="bg-slate-800/60 backdrop-blur-sm p-8 rounded-xl border border-slate-700/50 shadow-2xl shadow-cyan-500/5 w-full max-w-md">
                <h1 className="text-2xl font-bold text-cyan-400 mb-6 tracking-wide">TeleAPI</h1>

                {!authed ? (
                    <form onSubmit={handleKeySubmit} className="space-y-4">
                        <div>
                            <label className="text-sm font-medium text-slate-400 mb-1 flex items-center gap-1.5">
                                <KeyRound className="w-3.5 h-3.5" />
                                管理密钥
                            </label>
                            <input
                                type="password"
                                value={key}
                                onChange={(e) => setKey(e.target.value)}
                                className={inputClass}
                                placeholder="请输入管理密钥"
                            />
                        </div>
                        {error && <p className="text-rose-400 text-sm">{error}</p>}
                        <button type="submit" className={primaryBtn}>验证</button>
                    </form>
                ) : (
                    <div className="space-y-4">
                        <p className="text-emerald-400 text-sm">密钥验证通过</p>

                        {!show2fa && (
                            <>
                                <div className="flex border-b border-slate-700/50 mb-4">
                                    <button
                                        onClick={() => { setLoginMethod('qr'); setError(''); }}
                                        className={`flex-1 py-2 text-sm font-medium border-b-2 transition-colors flex items-center justify-center gap-1.5 ${
                                            loginMethod === 'qr'
                                                ? 'border-cyan-400 text-cyan-400'
                                                : 'border-transparent text-slate-500 hover:text-slate-300'
                                        }`}
                                    >
                                        <QrCode className="w-4 h-4" />
                                        扫码登录
                                    </button>
                                    <button
                                        onClick={() => { setLoginMethod('phone'); setError(''); }}
                                        className={`flex-1 py-2 text-sm font-medium border-b-2 transition-colors flex items-center justify-center gap-1.5 ${
                                            loginMethod === 'phone'
                                                ? 'border-cyan-400 text-cyan-400'
                                                : 'border-transparent text-slate-500 hover:text-slate-300'
                                        }`}
                                    >
                                        <Smartphone className="w-4 h-4" />
                                        手机号登录
                                    </button>
                                </div>

                                {loginMethod === 'qr' && (
                                    <>
                                        {!qrImage && qrStatus !== '2fa_required' && (
                                            <div className="space-y-3">
                                                <button onClick={startQrLogin} className={primaryBtn}>生成二维码</button>
                                            </div>
                                        )}

                                        {qrImage && qrStatus === 'waiting' && (
                                            <div className="text-center space-y-3">
                                                <p className="text-sm text-slate-400">请使用 Telegram 手机客户端扫码</p>
                                                <img src={qrImage} alt="QR Code" className="mx-auto w-48 h-48 rounded-lg" />
                                                <p className="text-xs text-slate-500">等待扫码...</p>
                                            </div>
                                        )}

                                        {qrStatus === 'expired' && (
                                            <div className="text-center space-y-3">
                                                <p className="text-sm text-amber-400">二维码已过期</p>
                                                <button onClick={refreshQr} className="py-2 px-4 bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 transition-colors">
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
                                                    <label className="block text-sm font-medium text-slate-400 mb-1">手机号</label>
                                                    <input
                                                        type="tel"
                                                        value={phone}
                                                        onChange={(e) => setPhone(e.target.value)}
                                                        className={inputClass}
                                                        placeholder="+8613800138000"
                                                    />
                                                    <p className="text-xs text-slate-500 mt-1">请使用国际格式，以 + 开头</p>
                                                </div>
                                                <button onClick={sendCode} className={primaryBtn}>发送验证码</button>
                                            </div>
                                        )}

                                        {phoneStatus === 'code_sent' && (
                                            <form onSubmit={verifyCode} className="space-y-3">
                                                <p className="text-sm text-emerald-400">验证码已发送至 {phone}</p>
                                                <input
                                                    type="text"
                                                    value={verificationCode}
                                                    onChange={(e) => setVerificationCode(e.target.value)}
                                                    className={inputClass}
                                                    placeholder="请输入验证码"
                                                    autoFocus
                                                />
                                                <button type="submit" className={primaryBtn}>验证</button>
                                                <button
                                                    type="button"
                                                    onClick={sendCode}
                                                    className="w-full py-1 text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
                                                >
                                                    重新发送
                                                </button>
                                            </form>
                                        )}

                                        {phoneStatus === 'expired' && (
                                            <div className="text-center space-y-3">
                                                <p className="text-sm text-amber-400">验证码已过期</p>
                                                <button onClick={sendCode} className="py-2 px-4 bg-cyan-600 text-white rounded-lg hover:bg-cyan-500 transition-colors">
                                                    重新发送
                                                </button>
                                            </div>
                                        )}

                                        {phoneStatus === 'error' && (
                                            <div className="space-y-3">
                                                <button
                                                    onClick={() => { setPhoneStatus(''); setError(''); }}
                                                    className="w-full py-2 border border-slate-600 rounded-lg text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition-colors"
                                                >
                                                    重试
                                                </button>
                                            </div>
                                        )}
                                    </>
                                )}

                                <button
                                    onClick={() => navigate('/')}
                                    className="w-full py-2 border border-slate-600 rounded-lg text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition-colors"
                                >
                                    跳过（已登录）
                                </button>
                            </>
                        )}

                        {show2fa && (
                            <form onSubmit={handle2fa} className="space-y-3">
                                <p className="text-sm text-amber-400 flex items-center gap-1.5">
                                    <ShieldCheck className="w-4 h-4" />
                                    需要两步验证密码
                                </p>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className={inputClass}
                                    placeholder="请输入两步验证密码"
                                />
                                <button type="submit" className={primaryBtn}>提交</button>
                            </form>
                        )}

                        {error && <p className="text-rose-400 text-sm">{error}</p>}
                    </div>
                )}
            </div>
        </div>
    );
}
