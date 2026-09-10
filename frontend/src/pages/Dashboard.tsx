import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Cpu,
    ShieldCheck,
    AlertTriangle,
    AlertOctagon,
    MapPin,
    ArrowRight,
    Activity,
    Play,
    Pause,
    Clock,
    X,
    Maximize2,
    Zap,
    Thermometer,
    Gauge,
    LayoutGrid
} from 'lucide-react';
import { SensorWidget } from '../components/SensorWidget';

interface DashboardAsset {
    id: string;
    name: string;
    location: string;
    status: string;
    sensors: {
        variable: string;
        unit: string;
        topic: string;
        thresholds?: {
            warning?: number;
            critical?: number;
            nominal?: number;
        };
    }[];
    motor_model?: {
        brand: string;
        model: string;
        power_hp: number;
    };
}

const Dashboard = () => {
    // Estados do Dashboard: Lista de ativos, leituras atuais e histórico temporal
    const [assets, setAssets] = useState<DashboardAsset[]>([]);
    const [telemetry, setTelemetry] = useState<Record<string, number>>({});
    const [lastActive, setLastActive] = useState<Record<string, number>>({});
    const [history, setHistory] = useState<Record<string, number[]>>({});
    const [loading, setLoading] = useState(true);
    const [expandedAsset, setExpandedAsset] = useState<DashboardAsset | null>(null);
    const [selectedSensor, setSelectedSensor] = useState<any>(null);
    const [simConfig, setSimConfig] = useState({ running: true, interval: 5 });

    const fetchDashboard = async () => {
        /**
         * Recuperação de Dados do Ecossistema:
         * Busca a visão consolidada de ativos, sensores e seus respectivos estados.
         */
        try {
            const res = await fetch('/api/assets/dashboard');
            if (res.ok) {
                const data = await res.json();
                setAssets(data);
            }
        } catch (e) {
            console.error("Erro ao buscar dados do dashboard:", e);
        } finally {
            setLoading(false);
        }
    };

    const fetchConfig = async () => {
        try {
            const res = await fetch('/api/config');
            if (res.ok) {
                const data = await res.json();
                setSimConfig(data);
            }
        } catch (e) { }
    };

    const updateConfig = async (newConfig: any) => {
        try {
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            });
            setSimConfig(newConfig);
        } catch (e) { }
    };

    useEffect(() => {
        fetchDashboard();
        fetchConfig();

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/ws/telemetry`;
        let ws: WebSocket | null = null;

        // Modo Simulador de Apresentação (Início Imediato sem esperar cair WS)
        if (!(window as any)._mockStartedDashboard) {
            (window as any)._mockStartedDashboard = true;
            const runSim = () => {
                setAssets(currentAssets => {
                    currentAssets.forEach(asset => {
                        if (!asset.sensors) return;
                        asset.sensors.forEach(s => {
                            const topicKey = s.topic;
                            const nominal = s.thresholds?.nominal || 50;
                            const critical = s.thresholds?.critical || (nominal * 1.5);
                            
                            const isAlert = Math.random() < 0.5;
                            let val = isAlert 
                                ? critical + (Math.random() * (critical * 0.2))
                                : nominal + (Math.random() * (critical - nominal) * 0.5);
                            val = parseFloat(val.toFixed(2));
                            
                            fetch('/api/telemetry/ingest', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ topic: topicKey, payload: { value: val } })
                            }).catch(() => {});
                            
                            setTelemetry(prev => ({ ...prev, [topicKey]: val }));
                            setLastActive(prev => ({ ...prev, [topicKey]: Date.now() }));
                            setHistory(prev => {
                                const newHistory = { ...prev };
                                const current = newHistory[topicKey] || [];
                                
                                // Pré-preenchimento "Viagem no Tempo" se estiver vazio
                                if (current.length === 0) {
                                    const fakePast = [];
                                    for(let i=0; i<19; i++) {
                                        const pastIsAlert = Math.random() < 0.1;
                                        let pastVal = pastIsAlert 
                                            ? critical + (Math.random() * (critical * 0.1))
                                            : nominal + (Math.random() * (critical - nominal) * 0.5);
                                        fakePast.push(parseFloat(pastVal.toFixed(2)));
                                    }
                                    newHistory[topicKey] = [...fakePast, val];
                                } else {
                                    newHistory[topicKey] = [...current, val].slice(-20);
                                }
                                return newHistory;
                            });
                        });
                    });
                    return currentAssets;
                });
            };
            runSim(); // Executa imediatamente
            setInterval(runSim, 15000);
        }

        const connectWS = () => {
            ws = new WebSocket(wsUrl);
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    const topicKey = data.topic;

                    if (topicKey) {
                        let val = 0;
                        if (data.value !== undefined) {
                            val = data.value;
                        } else if (data.payload && typeof data.payload === 'object' && data.payload.value !== undefined) {
                            val = data.payload.value;
                        } else {
                            val = parseFloat(data.payload) || 0;
                        }

                        setTelemetry(prev => ({ ...prev, [topicKey]: val }));
                        setLastActive(prev => ({ ...prev, [topicKey]: Date.now() }));
                        setHistory(prev => {
                            const newHistory = { ...prev };
                            const current = newHistory[topicKey] || [];
                            newHistory[topicKey] = [...current, val].slice(-20);
                            return newHistory;
                        });
                    }
                } catch (e) {
                    console.error("Erro no processamento de WebSocket:", e);
                }
            };
            ws.onclose = () => {
                setTimeout(connectWS, 10000); // Tenta reconectar a cada 10s
            };
        };

        connectWS();
        return () => ws?.close();
    }, []);

    const getStatus = (asset: DashboardAsset) => {
        let status = 'ok';
        asset.sensors.forEach(s => {
            const topicKey = s.topic;
            const val = telemetry[topicKey];
            if (val === undefined) return;

            const th = {
                warning: s.thresholds?.warning || 75,
                critical: s.thresholds?.critical || 90
            };

            if (val >= th.critical) status = 'critical';
            else if (val >= th.warning && status !== 'critical') status = 'warning';
        });
        return status;
    };

    const getStatusColor = (val: number, thresholds: any) => {
        if (!thresholds) return 'text-emerald-400';
        if (thresholds.critical && val >= thresholds.critical) return 'text-rose-500';
        if (thresholds.warning && val >= thresholds.warning) return 'text-amber-400';
        return 'text-emerald-400';
    };

    const getPulseColor = (val: number, thresholds: any) => {
        if (!thresholds) return 'rgba(16, 185, 129, 0.2)';
        if (thresholds.critical && val >= thresholds.critical) return 'rgba(244, 63, 94, 0.4)';
        if (thresholds.warning && val >= thresholds.warning) return 'rgba(251, 191, 36, 0.3)';
        return 'rgba(16, 185, 129, 0.2)';
    };

    const getStatusConfig = (status: string) => {
        switch (status) {
            case 'critical':
                return {
                    label: 'Risco Crítico',
                    color: 'text-red-500',
                    bg: 'bg-red-500/10',
                    border: 'border-red-500/20',
                    shadow: 'shadow-[0_0_30px_rgba(239,68,68,0.2)]',
                    icon: <AlertOctagon size={20} className="text-red-500" />
                };
            case 'warning':
                return {
                    label: 'Aviso / Atenção',
                    color: 'text-amber-500',
                    bg: 'bg-amber-500/10',
                    border: 'border-amber-500/20',
                    shadow: 'shadow-[0_0_30px_rgba(245,158,11,0.2)]',
                    icon: <AlertTriangle size={20} className="text-amber-500" />
                };
            default:
                return {
                    label: 'Operação Normal',
                    color: 'text-emerald-500',
                    bg: 'bg-emerald-500/10',
                    border: 'border-emerald-500/20',
                    shadow: 'shadow-[0_0_30px_rgba(16,185,129,0.2)]',
                    icon: <ShieldCheck size={20} className="text-emerald-500" />
                };
        }
    };

    // LÓGICA DE ALERTA NO PAINEL GERAL (Compartilhada via sessionStorage para evitar duplicados)
    useEffect(() => {
        assets.forEach(asset => {
            if (!asset.sensors) return;
            asset.sensors.forEach(s => {
                const topicKey = s.topic;
                const val = telemetry[topicKey];
                if (val !== undefined) {
                    const criticalTh = s.thresholds?.critical || 90;
                    const warningTh = s.thresholds?.warning || 75;
                    
                    let status = null;
                    let limit = 0;
                    
                    if (val >= criticalTh) {
                        status = 'PERIGO';
                        limit = criticalTh;
                    } else if (val >= warningTh) {
                        status = 'ATENÇÃO';
                        limit = warningTh;
                    }

                    if (status) {
                        const lastAlertStr = localStorage.getItem(`alert_${topicKey}_${status}`);
                        const lastAlert = lastAlertStr ? parseInt(lastAlertStr) : 0;
                        const now = Date.now();
                        // 60 segundos de cooldown por sensor/status para não enviar repetido
                        if (now - lastAlert > 60000) {
                            localStorage.setItem(`alert_${topicKey}_${status}`, now.toString());
                            fetch('/api/alerts/telegram', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    asset_name: asset.name,
                                    variable: s.variable,
                                    value: val,
                                    status: status,
                                    limit: limit,
                                    unit: s.unit || ""
                                })
                            }).catch(e => console.error("Falha de rede ao acionar alerta Telegram:", e));
                        }
                    }
                }
            });
        });
    }, [telemetry, assets]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="flex flex-col items-center gap-4">
                    <Activity className="text-[var(--theme-primary)] animate-pulse" size={48} />
                    <span className="text-[10px] font-black text-white/40 uppercase tracking-[0.5em]">Sincronizando Resumo Executivo</span>
                </div>
            </div>
        );
    }

    return (
        <div className="p-8 max-w-[1600px] mx-auto w-full space-y-12">
            <header className="relative py-12 px-10 bg-black/20 border border-white/5 rounded-[3rem] backdrop-blur-2xl overflow-hidden group">
                <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-8">
                    <div className="space-y-4">
                        <div className="flex items-center gap-3 mb-3">
                            <div className="w-2 h-2 rounded-full bg-[var(--theme-primary)] animate-pulse shadow-[0_0_10px_var(--theme-primary)]" />
                            <span className="text-[10px] font-black uppercase tracking-[0.4em] text-[var(--theme-primary)]">Industrial Health Overview</span>
                        </div>
                        <h1 className="text-5xl font-black text-white uppercase tracking-tighter leading-tight">
                            Painel Geral de Ativos
                        </h1>
                        <p className="text-white/40 text-sm font-medium max-w-xl uppercase tracking-wider">
                            Visão consolidada da saúde operacional de toda a planta industrial. Monitoramento de anomalias e status em tempo real.
                        </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-4 p-6 bg-white/5 rounded-[2rem] border border-white/10 backdrop-blur-md">
                        <div className="flex flex-col gap-1 mr-4">
                            <span className="text-[8px] font-black text-white/20 uppercase tracking-[0.2em]">Injeção de Histórico CSV</span>
                            <div className="flex items-center gap-2">
                                <div className={`w-1.5 h-1.5 rounded-full ${simConfig.running ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                                <span className={`text-[10px] font-black uppercase tracking-widest ${simConfig.running ? 'text-emerald-500' : 'text-red-500'}`}>
                                    {simConfig.running ? 'Ativa' : 'Desligada'}
                                </span>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 p-1 bg-black/20 rounded-xl border border-white/5">
                            <button
                                onClick={() => updateConfig({ ...simConfig, running: true })}
                                className={`p-3 rounded-lg transition-all ${simConfig.running ? 'bg-[var(--theme-primary)] text-black shadow-[0_0_15px_var(--theme-primary)]' : 'text-white/40 hover:text-white'}`}
                                title="Ativar Leitura do CSV"
                            >
                                <Play size={16} fill={simConfig.running ? "currentColor" : "none"} />
                            </button>
                            <button
                                onClick={() => updateConfig({ ...simConfig, running: false })}
                                className={`p-3 rounded-lg transition-all ${!simConfig.running ? 'bg-red-500 text-white shadow-[0_0_15px_rgba(239,68,68,0.4)]' : 'text-white/40 hover:text-white'}`}
                                title="Desativar Leitura do CSV"
                            >
                                <Pause size={16} fill={!simConfig.running ? "currentColor" : "none"} />
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {assets.map((asset, idx) => {
                    const status = getStatus(asset);
                    const config = getStatusConfig(status);

                    return (
                        <motion.div
                            key={asset.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className={`group relative bg-white/5 border ${config.border} p-8 rounded-[2.5rem] hover:bg-white/[0.08] transition-all cursor-default ${config.shadow}`}
                        >
                            <div className="flex justify-between items-start mb-10">
                                <div className="p-4 bg-white/5 rounded-2xl border border-white/5 text-[var(--theme-primary)] group-hover:scale-110 transition-transform">
                                    <Cpu size={28} />
                                </div>
                                <div className={`flex items-center gap-2 px-4 py-2 ${config.bg} rounded-full border ${config.border}`}>
                                    {config.icon}
                                    <span className={`text-[10px] font-black uppercase tracking-widest ${config.color}`}>
                                        {config.label}
                                    </span>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <h3 className="text-2xl font-black text-white uppercase tracking-tighter group-hover:text-[var(--theme-primary)] transition-colors">
                                    {asset.name}
                                </h3>
                                <div className="flex items-center gap-2 text-white/40">
                                    <MapPin size={12} />
                                    <span className="text-[10px] font-bold uppercase tracking-widest">{asset.location}</span>
                                </div>
                            </div>

                            {/* REMOVIDO: Sensores removidos conforme solicitação por design minimalista */}


                            <div className="mt-10 pt-8 border-t border-white/5 flex items-center justify-between">
                                <div className="flex flex-col">
                                    <span className="text-[9px] font-black text-white/20 uppercase tracking-widest">Sensores Ativos</span>
                                    <span className="text-lg font-black text-white">{asset.sensors.length}</span>
                                </div>
                                <button
                                    onClick={() => setExpandedAsset(asset)}
                                    className="flex items-center gap-2 text-[10px] font-black text-[var(--theme-primary)] uppercase tracking-widest hover:brightness-125 transition-all"
                                >
                                    Expandir <Maximize2 size={14} />
                                </button>
                            </div>

                            <div className={`absolute top-0 right-0 w-32 h-32 opacity-10 blur-3xl rounded-full -mr-16 -mt-16 transition-colors ${status === 'critical' ? 'bg-red-500' : status === 'warning' ? 'bg-amber-500' : 'bg-emerald-500'}`} />
                        </motion.div>
                    );
                })}

                {assets.length === 0 && (
                    <div className="col-span-full py-32 text-center border border-dashed border-white/10 bg-black/20 rounded-[3rem]">
                        <Activity size={48} className="mx-auto mb-6 text-white/10" />
                        <p className="text-white/20 uppercase font-black tracking-[0.3em] text-lg">Nenhum Ativo Detectado</p>
                        <p className="text-white/10 text-[10px] mt-4 uppercase font-bold tracking-widest">Aguardando provisionamento no módulo de Gêmeos Digitais</p>
                    </div>
                )}
            </div>

            {/* Modal Expandir */}
            <AnimatePresence>
                {expandedAsset && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-12 overflow-hidden">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setExpandedAsset(null)}
                            className="absolute inset-0 bg-black/80 backdrop-blur-xl"
                        />

                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.9, y: 20 }}
                            className="relative w-full max-w-[1400px] max-h-full bg-zinc-950 border border-white/10 rounded-[3rem] shadow-[0_0_100px_rgba(0,0,0,0.5)] overflow-y-auto overflow-x-hidden custom-scrollbar flex flex-col"
                        >
                            <div className="sticky top-0 z-20 flex items-center justify-between p-8 bg-zinc-950/80 backdrop-blur-md border-b border-white/5">
                                <div className="flex items-center gap-6">
                                    <div className="p-4 bg-[var(--theme-primary)]/10 rounded-2xl text-[var(--theme-primary)]">
                                        <Cpu size={32} />
                                    </div>
                                    <div>
                                        <h2 className="text-3xl font-black text-white uppercase tracking-tighter">{expandedAsset.name}</h2>
                                        <p className="text-[10px] text-white/40 font-bold uppercase tracking-[0.2em] flex items-center gap-2">
                                            <MapPin size={10} /> {expandedAsset.location} • STATUS EM TEMPO REAL
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setExpandedAsset(null)}
                                    className="p-4 hover:bg-white/5 text-white/40 hover:text-white transition-all rounded-2xl"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            <div className="p-8 md:p-12">
                                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                                    {/* Digital Twin View (SVG) */}
                                    <div className="lg:col-span-8 bg-black/40 rounded-[3rem] border border-white/5 p-8 relative overflow-hidden flex items-center justify-center min-h-[500px] backdrop-blur-2xl">
                                        <div className="absolute inset-0 bg-gradient-to-br from-[var(--theme-primary)]/5 via-transparent to-transparent opacity-50" />

                                        <svg viewBox="0 0 800 400" className="w-full max-w-2xl relative z-10">
                                            <motion.path
                                                d="M200 150 L600 150 L630 180 L630 320 L600 350 L200 350 L170 320 L170 180 Z"
                                                fill="none"
                                                stroke="rgba(255,255,255,0.15)"
                                                strokeWidth="2"
                                                animate={{ stroke: 'rgba(0,255,204,0.3)' }}
                                            />
                                            <motion.rect
                                                x="630" y="235" width="100" height="30"
                                                fill="rgba(255,255,255,0.05)"
                                                stroke="rgba(255,255,255,0.2)"
                                                animate={{ rotate: telemetry[`Forzy/telemetry/${expandedAsset.motor_model?.model}/rpm`] ? 360 : 0 }}
                                                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                                            />
                                            {[0, 1, 2, 3, 4, 5, 6].map(i => (
                                                <line key={i} x1={220 + i * 60} y1="150" x2={220 + i * 60} y2="130" stroke="rgba(255,255,255,0.1)" strokeWidth="4" />
                                            ))}

                                            {/* Dynamic Hotspots */}
                                            {expandedAsset.sensors.map((s: any, i: number) => {
                                                const topicKey = s.topic;
                                                const val = telemetry[topicKey] || 0;
                                                const isTemp = s.variable.toLowerCase().includes('temp');
                                                const isVib = s.variable.toLowerCase().includes('vib');

                                                if (isTemp) return (
                                                    <g key={i}>
                                                        <motion.circle
                                                            cx="400" cy="250" r="40"
                                                            fill={getPulseColor(val, s.thresholds)}
                                                            animate={{ scale: [1, 1.2, 1] }}
                                                            transition={{ repeat: Infinity, duration: 1.5 }}
                                                        />
                                                        <circle cx="400" cy="250" r="4" fill="white" />
                                                        <text x="400" y="220" textAnchor="middle" className="text-[10px] fill-white/40 font-black uppercase">Termal</text>
                                                    </g>
                                                );
                                                if (isVib) return (
                                                    <g key={i}>
                                                        <motion.circle
                                                            cx="580" cy="250" r="30"
                                                            fill={getPulseColor(val, s.thresholds)}
                                                            animate={{ x: [0, 2, -2, 0] }}
                                                            transition={{ repeat: Infinity, duration: 0.1 }}
                                                        />
                                                        <text x="580" y="210" textAnchor="middle" className="text-[10px] fill-white/40 font-black uppercase">Cinemática</text>
                                                    </g>
                                                );
                                                return null;
                                            })}
                                        </svg>

                                        <div className="absolute top-8 left-8 flex flex-col gap-3">
                                            {expandedAsset.sensors.slice(0, 3).map((s, i) => {
                                                const val = telemetry[s.topic] || 0;
                                                return (
                                                    <motion.div
                                                        key={i}
                                                        initial={{ x: -20, opacity: 0 }}
                                                        animate={{ x: 0, opacity: 1 }}
                                                        transition={{ delay: i * 0.1 }}
                                                        className="bg-black/60 border border-white/10 p-4 rounded-2xl backdrop-blur-md min-w-[180px]"
                                                    >
                                                        <p className="text-[9px] text-white/40 font-bold uppercase tracking-wider mb-1">{s.variable}</p>
                                                        <div className="flex items-end gap-2">
                                                            <span className={`text-xl font-black ${getStatusColor(val, s.thresholds)}`}>
                                                                {val.toFixed(1)}
                                                            </span>
                                                            <span className="text-[9px] text-white/40 font-bold pb-1">{s.unit}</span>
                                                        </div>
                                                    </motion.div>
                                                );
                                            })}
                                        </div>
                                    </div>

                                    {/* Asset Info & Thresholds */}
                                    <div className="lg:col-span-4 space-y-6">
                                        <div className="bg-white/5 border border-white/10 rounded-[2.5rem] p-8 backdrop-blur-xl">
                                            <h3 className="text-[10px] font-black text-[var(--theme-primary)] uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                                                <Zap size={14} /> Ficha Técnica
                                            </h3>
                                            <div className="space-y-4">
                                                {[
                                                    { label: 'Fabricante', val: expandedAsset.motor_model?.brand || 'WEG' },
                                                    { label: 'Modelo', val: expandedAsset.motor_model?.model || '--' },
                                                    { label: 'Potência', val: `${expandedAsset.motor_model?.power_hp} HP` },
                                                    { label: 'ID Sistema', val: expandedAsset.id.slice(0, 8).toUpperCase() },
                                                ].map((row, idx) => (
                                                    <div key={idx} className="flex justify-between border-b border-white/5 pb-3">
                                                        <span className="text-[10px] text-white/40 uppercase font-bold">{row.label}</span>
                                                        <span className="text-[10px] text-white font-black uppercase">{row.val}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="bg-black/40 border border-white/10 rounded-[2.5rem] p-8">
                                            <h3 className="text-[10px] font-black text-rose-500 uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                                                <ShieldCheck size={14} /> Health Monitoring
                                            </h3>
                                            <div className="space-y-6">
                                                {expandedAsset.sensors.map((s, i) => {
                                                    const val = telemetry[s.topic] || 0;
                                                    const th = s.thresholds || { warning: 75, critical: 90 };
                                                    const pct = Math.min((val / (th.critical || 100)) * 100, 100);
                                                    return (
                                                        <div key={i} className="space-y-2">
                                                            <div className="flex justify-between items-end">
                                                                <span className="text-[9px] text-white/60 font-black uppercase tracking-widest">{s.variable}</span>
                                                                <span className="text-[9px] text-white/40 font-bold">{val.toFixed(1)} / {th.critical} {s.unit}</span>
                                                            </div>
                                                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                                                <motion.div
                                                                    className={`h-full rounded-full ${pct > 90 ? 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.3)]' : pct > 75 ? 'bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.3)]' : 'bg-[var(--theme-primary)] shadow-[0_0_10px_rgba(0,255,204,0.3)]'}`}
                                                                    initial={{ width: 0 }}
                                                                    animate={{ width: `${pct}%` }}
                                                                />
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Advanced Sensor Widgets */}
                                <div className="mt-12">
                                    <div className="flex items-center gap-4 mb-8">
                                        <LayoutGrid size={20} className="text-[var(--theme-primary)]" />
                                        <h3 className="text-xl font-black text-white uppercase tracking-tighter">Telemetria Avançada</h3>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                        {expandedAsset.sensors.map((s, i) => {
                                            const val = telemetry[s.topic] || 0;
                                            const hist = history[s.topic] || [];
                                            const th = s.thresholds || { critical: 100 };
                                            return (
                                                <SensorWidget
                                                    key={i}
                                                    title={s.variable}
                                                    unit={s.unit}
                                                    currentValue={val}
                                                    history={hist}
                                                    min={0}
                                                    max={(th.critical || 100) * 1.2}
                                                    icon={<Zap size={16} />}
                                                />
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Dashboard;





