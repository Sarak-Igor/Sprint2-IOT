import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

// 0. CSS PRECEDENCE
import './index.css'
import '@sarak/lib-ui-core/sarak.css'

// Imports Sarak v10.1 Sovereign
import {
    SarakUIProvider,
    SarakShell,
    registerLocalComponent
} from '@sarak/lib-ui-core';

// 1. DNA E COMPONENTES LOCAIS
import sarakManifest from './sarak.manifest.json';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import History from './pages/History';
import Vision from './pages/Vision';
import Knowledge from './pages/Knowledge';

const SYSTEM_ID = "Forzy";
const SYSTEM_VISUAL_NAME = sarakManifest.system.name;

// Injeção de Identidade Global
(window as any).__SARAK_SYSTEM__ = SYSTEM_ID;

// 2. REGISTRO INDUSTRIAL (Plug & Play)
// Vinculamos os componentes locais aos IDs definidos no sarak.manifest.json
registerLocalComponent('dashboard', Dashboard);
registerLocalComponent('assets', Assets);
registerLocalComponent('history', History);
registerLocalComponent('vision', Vision);
registerLocalComponent('knowledge', Knowledge);

// 3. MOCK DE AUTENTICAÇÃO E CONTEXTO
const AuthProvider = ({ children }: any) => <>{children}</>;
const ProtectedRoute = ({ children }: any) => <>{children}</>;

const SarakApp = () => {
    return (
        <SarakShell
            brand={{
                name: SYSTEM_VISUAL_NAME,
                logo: 'https://img.icons8.com/neon/96/engine.png'
            }}
            user={{ id: 'admin', name: 'Forzy Operator', role: 'admin' }}
            token="sovereign-token"
            layout="sovereign"
            mode="sovereign"
        />
    );
};

const AppContent = () => {
    // Garantir que o modo soberano seja aplicado ao body
    React.useEffect(() => {
        document.body.classList.add('dark', 'sarak-sovereign');
        document.documentElement.setAttribute('data-sarak-theme', sarakManifest.design.theme);
        document.documentElement.setAttribute('data-sarak-layout', 'sovereign');
    }, []);

    return (
        <SarakUIProvider
            config={{
                systemId: SYSTEM_ID,
                design: sarakManifest.design,
                discovery: {
                    mode: 'local',
                    autoRegister: true // Agora a biblioteca lê o manifesto automaticamente
                }
            }}
            options={{
                manifest: sarakManifest,
                debug: true
            }}
        >
            <Routes>
                <Route path="/*" element={<ProtectedRoute><SarakApp /></ProtectedRoute>} />
            </Routes>
        </SarakUIProvider>
    );
};

const App = () => {
    return (
        <BrowserRouter>
            <AuthProvider>
                <AppContent />
            </AuthProvider>
        </BrowserRouter>
    );
};

// Renderização Limpa e Única (Padrão Industrial)
const rootElement = document.getElementById('root');
if (rootElement) {
    ReactDOM.createRoot(rootElement).render(
        <React.StrictMode>
            <App />
        </React.StrictMode>,
    );
}
