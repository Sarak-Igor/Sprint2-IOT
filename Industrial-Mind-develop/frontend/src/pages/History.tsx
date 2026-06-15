import React, { useState, useEffect } from 'react';
import { Filter, Download, ArrowUpRight, Clock } from 'lucide-react';

const History = () => {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedRow, setSelectedRow] = useState<any | null>(null);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const response = await fetch('/api/telemetry?limit=50');
                const result = await response.json();
                setData(result);
            } catch (e) {
                console.error("Erro ao buscar histórico:", e);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    return (
        <div className="flex flex-col gap-6 p-6">
            <header className="flex justify-between items-center bg-theme-card border-theme p-6 rounded-theme">
                <div>
                    <h1 className="text-2xl font-black text-white uppercase tracking-tighter">Histórico Operacional</h1>
                    <p className="text-xs text-white/40 uppercase font-bold tracking-widest mt-1">Registro de Séries Temporais — Banco Neon</p>
                </div>
                <div className="flex gap-3">
                    <button className="flex items-center gap-2 bg-white/5 hover:bg-white/10 text-white/60 border border-white/10 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all">
                        <Filter size={14} /> Filtros
                    </button>
                    <button className="flex items-center gap-2 bg-[var(--theme-primary)] hover:opacity-80 text-black px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all">
                        <Download size={14} /> Exportar CSV
                    </button>
                </div>
            </header>

            <div className="bg-theme-card border-theme p-6 rounded-theme overflow-hidden">
                {loading ? (
                    <div className="py-20 text-center text-white/20 uppercase font-black tracking-[0.2em] text-xs">Carregando dados do Neon...</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-white/5 text-[10px] font-black text-white/40 uppercase tracking-widest">
                                    <th className="p-4">Timestamp</th>
                                    <th className="p-4">TAG</th>
                                    <th className="p-4 text-center">Temperatura (°C)</th>
                                    <th className="p-4 text-center">Vibração (mm/s)</th>
                                    <th className="p-4">Status</th>
                                    <th className="p-4 text-right">Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.map((row) => (
                                    <tr key={row.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors group">
                                        <td className="p-4 text-[11px] font-mono text-white/60">
                                            {new Date(row.timestamp).toLocaleString()}
                                        </td>
                                        <td className="p-4 text-xs font-black text-white">
                                            {row.device_id || 'WEG_W22_01'}
                                        </td>
                                        <td className="p-4 text-sm font-bold text-white text-center">
                                            {(row.temp_windings || row.temp || 0).toFixed(1)}
                                        </td>
                                        <td className="p-4 text-sm font-bold text-white text-center">
                                            {(row.vibration_rms || row.vibration || 0).toFixed(2)}
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-[9px] font-black uppercase tracking-widest ${(row.temp_windings > 48)
                                                    ? 'bg-red-500/10 text-red-500 border border-red-500/20'
                                                    : 'bg-[var(--theme-success-bg)] text-[var(--theme-success)] border border-[var(--theme-success-border)]'
                                                }`}>
                                                {row.temp_windings > 48 ? 'Warning' : 'Normal'}
                                            </span>
                                        </td>
                                        <td className="p-4 text-right">
                                            <button
                                                onClick={() => setSelectedRow(row)}
                                                className="p-2 bg-white/5 rounded-lg text-white/20 group-hover:text-white group-hover:bg-[var(--theme-primary-bg)] transition-all"
                                            >
                                                <ArrowUpRight size={14} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Modal de Detalhes do Registro */}
            {selectedRow && (
                <div
                    className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-sm"
                    onClick={() => setSelectedRow(null)}
                >
                    <div
                        className="w-full max-w-xl bg-theme-card border-theme p-8 rounded-3xl shadow-2xl"
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="flex justify-between items-center mb-6">
                            <div>
                                <h2 className="text-xl font-black text-white uppercase tracking-tight">Detalhes da Coleta</h2>
                                <p className="text-[10px] text-white/40 uppercase font-bold tracking-widest mt-1">Payload bruto do banco de dados</p>
                            </div>
                            <button
                                onClick={() => setSelectedRow(null)}
                                className="text-white/20 hover:text-white transition-colors"
                            >
                                <Clock size={20} />
                            </button>
                        </div>
                        <div className="bg-black/40 rounded-2xl p-6 border border-white/5 max-h-[60vh] overflow-auto">
                            <pre className="text-[11px] font-mono text-[var(--theme-success)] leading-relaxed">
                                {JSON.stringify(selectedRow, null, 2)}
                            </pre>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default History;

