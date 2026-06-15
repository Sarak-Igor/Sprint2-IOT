import React, { useState, useEffect } from 'react';
import {
    SarakStats,
    SarakChart,
    ExpandableCard
} from '@sarak/lib-ui-core';
import {
    Activity,
    Cpu,
    Zap,
    Thermometer,
    ShieldCheck,
    AlertTriangle,
    Pause,
    Play,
    Clock,
    ZapOff,
    Waves
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Dashboard = () => {
    const [isSimulating, setIsSimulating] = useState(true);
    const [simInterval, setSimInterval] = useState(5);
    const [latestData, setLatestData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    // Sincronização com o Simulador Backend
    const fetchConfig = async () => {
        try {
            const res = await fetch('/api/config');
            if (res.ok) {
                const data = await res.json();
                setIsSimulating(data.running);
                setSimInterval(data.interval);
            }
        } catch (e) {
            console.error("Erro ao buscar config do simulador:", e);
        }
    };

    const fetchLatestTelemetry = async () => {
        try {
            const res = await fetch('/api/telemetry?limit=1');
            if (res.ok) {
                const data = await res.json();
                if (data && data.length > 0) {
                    setLatestData(data[0]);
                }
            }
        } catch (e) {
            console.error("Erro ao buscar telemetria:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConfig();
        fetchLatestTelemetry();

        // Polling para telemetria em tempo real
        const interval = setInterval(() => {
            fetchLatestTelemetry();
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    const toggleSimulation = async () => {
        const newState = !isSimulating;
        setIsSimulating(newState);
        try {
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ running: newState, interval: simInterval })
            });
        } catch (e) {
            console.error("Erro ao alternar simulação:", e);
        }
    };

    const updateInterval = async (val: number) => {
        setSimInterval(val);
        try {
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ running: isSimulating, interval: val })
            });
        } catch (e) {
            console.error("Erro ao atualizar intervalo:", e);
        }
    };

    return (
        <div className="flex flex-col gap-6 p-6 min-h-screen bg-theme-bg">
            {/* Header com Controles Operacionais */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-theme-card border-theme p-6 rounded-theme shadow-2xl">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-[var(--theme-primary)]/10 rounded-2xl border border-[var(--theme-primary)]/20">
                        <Cpu className="text-[var(--theme-primary)] animate-pulse" size={24} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-white uppercase tracking-tighter leading-none">Motor Industrial WEG W22</h2>
                        <p className="text-[10px] text-white/40 uppercase font-bold tracking-[0.2em] mt-2">ID do Ativo: #FORZY-W22-001 • Gêmeo Digital Ativo</p>
                    </div>
                </div>

                <div className="flex items-center gap-4 bg-black/40 p-2 rounded-2xl border border-white/5 backdrop-blur-sm">
                    <div className="flex items-center gap-3 px-4 border-r border-white/10">
                        <Clock size={14} className="text-white/40" />
                        <select
                            value={simInterval}
                            onChange={(e) => updateInterval(Number(e.target.value))}
                            className="bg-transparent text-[11px] font-black text-white uppercase outline-none cursor-pointer hover:text-[var(--theme-primary)] transition-colors"
                        >
                            <option value={2}>Fluxo: 2s</option>
                            <option value={5}>Fluxo: 5s</option>
                            <option value={10}>Fluxo: 10s</option>
                            <option value={30}>Fluxo: 30s</option>
                        </select>
                    </div>
                    <button
                        onClick={toggleSimulation}
                        className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-[0.1em] transition-all duration-500 shadow-lg ${isSimulating
                                ? 'bg-[var(--theme-success-bg)] text-[var(--theme-success)] border border-[var(--theme-success-border)] shadow-[var(--theme-success)]/10'
                                : 'bg-[var(--theme-warning-bg)] text-[var(--theme-warning)] border border-[var(--theme-warning-border)] shadow-[var(--theme-warning)]/10'
                            }`}
                    >
                        {isSimulating ? <><Pause size={12} fill="currentColor" /> Operando</> : <><Play size={12} fill="currentColor" /> Pausado</>}
                    </button>
                </div>
            </div>

            {/* Top Operational Metrics - Stats Component */}
            <SarakStats
                endpoint="telemetry/stats"
                mapping={{
                    temp: "Temperatura",
                    vibration: "Vibração",
                    power: "Consumo Ativo",
                    status: "Status"
                }}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Central Digital Twin View */}
                <div className="lg:col-span-2">
                    <ExpandableCard
                        title="Perspectiva do Gêmeo Digital"
                        baseHeight={600}
                        iconContent={<Activity className="text-[var(--theme-primary)]" size={18} />}
                    >
                        <div className="relative w-full h-full min-h-[500px] overflow-hidden rounded-xl bg-black/60 border border-white/10 group">
                            {/* Industrial Visualizer - 3D Mockup */}
                            <img
                                src="https://images.unsplash.com/photo-1621905235294-7500bed49cb3?auto=format&fit=crop&q=80&w=1600"
                                alt="Motor WEG W22"
                                className="w-full h-full object-cover opacity-40 grayscale group-hover:grayscale-0 transition-all duration-1000 scale-105 group-hover:scale-100"
                            />

                            {/* Scanning Overlay Effect */}
                            <div className="absolute inset-0 bg-gradient-to-t from-[var(--theme-primary)]/10 to-transparent pointer-events-none" />
                            <div className="absolute top-0 left-0 w-full h-1 bg-[var(--theme-primary)]/20 animate-scan pointer-events-none" />

                            {/* Telemetry Overlays - Positioned on parts of the motor */}
                            <AnimatePresence mode="wait">
                                {latestData && (
                                    <>
                                        {/* Winding Temperature */}
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.9 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="absolute top-[30%] left-[40%] cursor-help"
                                        >
                                            <div className="bg-black/80 backdrop-blur-xl border border-white/20 p-4 rounded-2xl flex items-center gap-4 shadow-2xl hover:border-[var(--theme-primary)]/50 transition-colors">
                                                <div className={`p-2 rounded-lg ${latestData.temp_windings > 60 ? 'bg-red-500/20 text-red-400' : 'bg-orange-500/20 text-orange-400'}`}>
                                                    <Thermometer size={16} />
                                                </div>
                                                <div>
                                                    <p className="text-[9px] text-white/40 uppercase font-black tracking-widest">Enrolamentos</p>
                                                    <p className="text-xl font-black text-white mt-0.5">{latestData.temp_windings.toFixed(1)}°C</p>
                                                </div>
                                            </div>
                                        </motion.div>

                                        {/* Vibration RMS */}
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.9 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="absolute bottom-[40%] right-[30%]"
                                        >
                                            <div className="bg-black/80 backdrop-blur-xl border border-white/20 p-4 rounded-2xl flex items-center gap-4 shadow-2xl hover:border-[var(--theme-primary)]/50 transition-colors">
                                                <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                                                    <Waves size={16} />
                                                </div>
                                                <div>
                                                    <p className="text-[9px] text-white/40 uppercase font-black tracking-widest">Vibração RMS</p>
                                                    <p className="text-xl font-black text-white mt-0.5">{latestData.vibration_rms.toFixed(2)}<span className="text-[10px] ml-1 opacity-40">mm/s</span></p>
                                                </div>
                                            </div>
                                        </motion.div>

                                        {/* Main Voltage */}
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.9 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="absolute top-[15%] right-[15%]"
                                        >
                                            <div className="bg-black/80 backdrop-blur-xl border border-white/20 p-4 rounded-2xl flex items-center gap-4 shadow-2xl hover:border-[var(--theme-primary)]/50 transition-colors">
                                                <div className="p-2 bg-yellow-500/20 rounded-lg text-yellow-400">
                                                    <Zap size={16} />
                                                </div>
                                                <div>
                                                    <p className="text-[9px] text-white/40 uppercase font-black tracking-widest">Tensão de Rede</p>
                                                    <p className="text-xl font-black text-white mt-0.5">{latestData.voltage_v.toFixed(0)}V</p>
                                                </div>
                                            </div>
                                        </motion.div>
                                    </>
                                )}
                            </AnimatePresence>

                            {/* Status Bottom Bar */}
                            <div className="absolute bottom-6 left-6 right-6 flex items-center justify-between bg-black/80 backdrop-blur-xl px-6 py-4 rounded-2xl border border-white/10 shadow-2xl">
                                <div className="flex items-center gap-4">
                                    <div className="relative">
                                        <div className={`w-3 h-3 rounded-full animate-pulse ${isSimulating ? 'bg-[var(--theme-success)] shadow-[0_0_15px_var(--theme-success)]' : 'bg-[var(--theme-warning)] shadow-[0_0_15px_var(--theme-warning)]'}`} />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-white uppercase tracking-wider">
                                            {isSimulating ? 'Operação em Regime Nominal' : 'Sistema em Standby / Pausado'}
                                        </p>
                                        <p className="text-[9px] text-white/40 font-bold uppercase mt-1">Conformidade com Norma ISO 10816-3</p>
                                    </div>
                                </div>
                                <div className="flex gap-4">
                                    <div className="text-right">
                                        <p className="text-[9px] text-white/40 uppercase font-black">RPM Estimado</p>
                                        <p className="text-sm font-black text-white">{isSimulating ? '1785 RPM' : '0 RPM'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </ExpandableCard>
                </div>

                {/* Right Column: Alerts & Analysis */}
                <div className="flex flex-col gap-6">
                    <ExpandableCard title="Análise de Tendência" baseHeight={300}>
                        <div className="p-2">
                            <SarakChart
                                endpoint="telemetry"
                                label="Temperatura de Enrolamento"
                                color="var(--theme-primary)"
                            />
                        </div>
                    </ExpandableCard>

                    {/* Operational Health Card */}
                    <div className="bg-theme-card border-theme p-6 rounded-theme flex flex-col gap-5 shadow-xl">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3 text-[var(--theme-primary)]">
                                <ShieldCheck size={20} />
                                <h4 className="text-xs font-black uppercase tracking-widest text-white">Saúde do Ativo</h4>
                            </div>
                            <span className="px-3 py-1 bg-[var(--theme-success)]/10 text-[var(--theme-success)] text-[9px] font-black uppercase rounded-full border border-[var(--theme-success)]/20">98.2%</span>
                        </div>

                        <div className="space-y-4">
                            <div className="flex flex-col gap-2">
                                <div className="flex justify-between text-[9px] font-black uppercase text-white/40">
                                    <span>Eficiência Térmica</span>
                                    <span className="text-white">94%</span>
                                </div>
                                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                    <div className="h-full bg-[var(--theme-primary)] w-[94%]" />
                                </div>
                            </div>
                            <div className="flex flex-col gap-2">
                                <div className="flex justify-between text-[9px] font-black uppercase text-white/40">
                                    <span>Índice de Vibração</span>
                                    <span className="text-white">Excelente</span>
                                </div>
                                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 w-[12%]" />
                                </div>
                            </div>
                        </div>

                        <p className="text-[11px] text-white/40 leading-relaxed font-medium bg-white/5 p-3 rounded-xl border border-white/5">
                            Nenhum desvio crítico detectado. Próxima inspeção termográfica recomendada para daqui a 12 dias conforme histórico de operação.
                        </p>
                    </div>

                    {/* Quick Action / Maintenance */}
                    <AnimatePresence>
                        {latestData && latestData.temp_windings > 70 && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: 20 }}
                                className="bg-[var(--theme-warning-bg)] border border-[var(--theme-warning-border)] p-6 rounded-theme flex flex-col gap-4 shadow-2xl shadow-orange-500/10"
                            >
                                <div className="flex items-center gap-2 text-[var(--theme-warning)]">
                                    <AlertTriangle size={18} />
                                    <h4 className="text-xs font-black uppercase tracking-widest">Alerta Térmico</h4>
                                </div>
                                <p className="text-[11px] text-[var(--theme-warning)] opacity-90 leading-relaxed font-bold">
                                    Temperatura crítica detectada nos enrolamentos. Verifique o sistema de refrigeração e a carga do motor imediatamente.
                                </p>
                                <button className="w-full bg-[var(--theme-warning)] text-black py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:brightness-110 transition-all">
                                    Iniciar Checklist de Emergência
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            <style dangerouslySetInnerHTML={{
                __html: `
                @keyframes scan {
                    0% { transform: translateY(0); }
                    100% { transform: translateY(600px); }
                }
                .animate-scan {
                    animation: scan 4s linear infinite;
                }
            ` }} />
        </div>
    );
};

export default Dashboard;



