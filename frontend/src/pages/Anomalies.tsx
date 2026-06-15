import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Clock, Activity, CheckCircle2, Filter } from 'lucide-react';

const Anomalies = () => {
    const [anomalies, setAnomalies] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAnomalies = async () => {
            try {
                const res = await fetch('/api/assets/anomalies');
                const data = await res.json();
                
                if (Array.isArray(data)) {
                    setAnomalies(data);
                } else {
                    setAnomalies([]);
                }
            } catch (err) {
                console.error("Erro ao buscar anomalias:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchAnomalies();
        const interval = setInterval(fetchAnomalies, 5000); // Polling a cada 5s
        return () => clearInterval(interval);
    }, []);

    const getSeverityStyles = (severity: string) => {
        if (severity === 'critical') return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
        return 'bg-amber-400/10 text-amber-400 border-amber-400/20';
    };

    return (
        <div className="p-8 space-y-8 max-w-[1200px] mx-auto">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
                        Log de <span className="text-[var(--theme-primary)]">Anomalias</span>
                    </h1>
                    <p className="text-white/40 text-xs font-bold uppercase tracking-widest mt-2">Detecção Preditiva & Eventos Críticos</p>
                </div>
                
                <button className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl border border-white/10 transition-colors">
                    <Filter size={20} className="text-white/60" />
                </button>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {loading ? (
                    <div className="p-20 text-center text-white/20 uppercase font-black tracking-widest">Sincronizando com Banco Industrial...</div>
                ) : anomalies.length === 0 ? (
                    <div className="p-20 bg-white/5 rounded-[2rem] border border-dashed border-white/10 text-center">
                        <CheckCircle2 size={48} className="mx-auto mb-4 text-emerald-500/20" />
                        <h3 className="text-white/60 font-black uppercase tracking-tighter">Nenhuma Anomalia Detectada</h3>
                        <p className="text-white/20 text-[10px] uppercase font-bold mt-1">Todos os ativos operando dentro dos limites nominais</p>
                    </div>
                ) : (
                    anomalies.map((anom, idx) => (
                        <motion.div
                            key={anom.id}
                            initial={{ x: -20, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: idx * 0.05 }}
                            className={`p-6 rounded-[2rem] border backdrop-blur-md flex items-center justify-between group ${getSeverityStyles(anom.severity)}`}
                        >
                            <div className="flex items-center gap-6">
                                <div className={`p-4 rounded-2xl border ${anom.severity === 'critical' ? 'bg-rose-500/20 border-rose-500/30' : 'bg-amber-400/20 border-amber-400/30'}`}>
                                    <AlertTriangle size={24} />
                                </div>
                                
                                <div>
                                    <div className="flex items-center gap-3 mb-1">
                                        <span className="text-xs font-black uppercase tracking-tighter text-white">{anom.asset_name}</span>
                                        <div className="w-1 h-1 rounded-full bg-white/20" />
                                        <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-md ${anom.severity === 'critical' ? 'bg-rose-500 text-white' : 'bg-amber-400 text-black'}`}>
                                            {anom.severity === 'critical' ? 'Perigo' : 'Aviso'}
                                        </span>
                                        <div className="w-1 h-1 rounded-full bg-white/20" />
                                        <span className="text-[10px] font-bold uppercase opacity-60">{anom.variable_name}</span>
                                    </div>
                                    <h4 className="text-lg font-black uppercase tracking-tight">
                                        Valor Excedido: {anom.value.toFixed(2)} (Limite: {anom.threshold})
                                    </h4>
                                </div>
                            </div>

                            <div className="text-right">
                                <div className="flex items-center justify-end gap-2 text-[10px] font-black uppercase opacity-60 mb-2">
                                    <Clock size={12} />
                                    {new Date(anom.timestamp).toLocaleString()}
                                </div>
                                <div className="flex gap-2">
                                    {anom.is_resolved ? (
                                        <span className="px-3 py-1 bg-emerald-500/20 text-emerald-500 rounded-full text-[9px] font-black uppercase">Resolvido</span>
                                    ) : (
                                        <button className="px-4 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded-xl text-[9px] font-black uppercase transition-all">
                                            Marcar como Lido
                                        </button>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    );
};

export default Anomalies;
