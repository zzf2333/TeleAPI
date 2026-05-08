import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { getApiKey } from './api/client';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Channels from './pages/Channels';
import Messages from './pages/Messages';
import SyncJobs from './pages/SyncJobs';
import WebhookLogs from './pages/WebhookLogs';
import ConfigCheck from './pages/ConfigCheck';

function AuthGuard({ children }: { children: React.ReactNode }) {
    if (!getApiKey()) {
        return <Navigate to="/login" replace />;
    }
    return <>{children}</>;
}

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                    path="/"
                    element={
                        <AuthGuard>
                            <Layout />
                        </AuthGuard>
                    }
                >
                    <Route index element={<Dashboard />} />
                    <Route path="channels" element={<Channels />} />
                    <Route path="messages" element={<Messages />} />
                    <Route path="sync-jobs" element={<SyncJobs />} />
                    <Route path="webhook-logs" element={<WebhookLogs />} />
                    <Route path="config-check" element={<ConfigCheck />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}
