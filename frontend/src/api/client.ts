const API_KEY_STORAGE = 'teleapi_admin_key';

export function getApiKey(): string {
    return localStorage.getItem(API_KEY_STORAGE) || '';
}

export function setApiKey(key: string) {
    localStorage.setItem(API_KEY_STORAGE, key);
}

export function clearApiKey() {
    localStorage.removeItem(API_KEY_STORAGE);
}

export async function api<T = unknown>(path: string, options?: RequestInit): Promise<T> {
    const key = getApiKey();
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...(options?.headers as Record<string, string>),
    };
    if (key) {
        headers['Authorization'] = `Bearer ${key}`;
    }

    const res = await fetch(path, { ...options, headers });

    if (res.status === 401 || res.status === 403) {
        clearApiKey();
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || body.detail || `HTTP ${res.status}`);
    }

    return res.json();
}
