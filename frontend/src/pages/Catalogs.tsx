import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Box, Cpu, Activity, Trash2, Plus, Info, Shield, Zap, Thermometer, Gauge } from 'lucide-react';

const Catalogs = () => {
    const [activeTab, setActiveTab] = useState<'models' | 'variables' | 'sensors'>('models');
    const [data, setData] = useState<any>({ models: [], variables: [], sensors: [] });
    const [selectedModel, setSelectedModel] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [modelsRes, varsRes, sensorsRes] = await Promise.all([
                fetch('/api/assets/models'),
                fetch('/api/assets/variables'),
                fetch('/api/assets/sensors')
            ]);

            setData({
                models: await modelsRes.json(),
                variables: await varsRes.json(),
                sensors: await sensorsRes.json()
            });
        } catch (err) {
            console.error("Erro ao carregar catálogo:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (type: string, id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        
        // Mapeamento amigável de nomes para o confirm
        const typeNames: Record<string, string> = {
            'models': 'este Modelo de Motor',
            'variables': 'esta Variável de Dado',
            'sensors': 'este Sensor Hardware'
        };

        if (!confirm(`Deseja realmente remover ${typeNames[type] || 'este item'} do catálogo?`)) return;
        
        try {
            const res = await fetch(`/api/assets/${type}/${id}`, { method: 'DELETE' });
            if (res.ok) {
                // Se o modelo selecionado for o que foi deletado, fecha o modal
                if (type === 'models' && selectedModel?.id === id) {
                    setSelectedModel(null);
                }
                loadData();
            } else {
                const error = await res.json();
                // Tratamento especial para erros de integridade (Foreign Key)
                if (res.status === 400 || res.status === 409 || (error.detail && error.detail.includes('ForeignKey'))) {
                    alert(`Não é possível remover este item pois ele está sendo utilizado por um Gêmeo Digital ativo. Remova os ativos vinculados primeiro.`);
                } else {
                    alert(`Erro ao remover: ${error.detail || 'Erro desconhecido'}`);
                }
            }
        } catch (err) {
            console.error("Erro na deleção:", err);
            alert("Erro de comunicação com o servidor.");
        }
    };

    const TabButton = ({ id, label, icon: Icon }: any) => (
        <button
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-3 px-8 py-4 rounded-2xl transition-all duration-500 border ${
                activeTab === id 
                ? 'bg-[var(--theme-primary)] text-black border-[var(--theme-primary)] shadow-[0_0_20px_var(--theme-primary)]' 
                : 'bg-white/5 text-white/40 border-white/5 hover:bg-white/10 hover:text-white'
            }`}
        >
            <Icon size={16} />
            <span className="text-[10px] font-black uppercase tracking-[0.2em]">{label}</span>
        </button>
    );

    return (
        <div className="p-8 space-y-8 max-w-[1400px] mx-auto">
            {/* Header */}
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
                        Catálogo Industrial
                    </h1>
                    <p className="text-xs text-white/40 font-medium uppercase tracking-wider mt-1">
                        Gestão soberana de modelos, sensores e variáveis operacionais.
                    </p>
                </div>
                <button className="flex items-center gap-2 px-6 py-3 bg-white text-black rounded-xl font-black text-[10px] uppercase tracking-wider hover:bg-[var(--theme-primary)] transition-colors">
                    <Plus size={14} />
                    Novo Item
                </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 p-2 bg-black/40 rounded-3xl border border-white/5 backdrop-blur-xl">
                <TabButton id="models" label="Modelos de Motor" icon={Box} />
                <TabButton id="variables" label="Variáveis de Dados" icon={Activity} />
                <TabButton id="sensors" label="Sensores Hardware" icon={Cpu} />
            </div>

            {/* List Table */}
            <div className="bg-black/40 border border-white/5 rounded-[2.5rem] overflow-hidden backdrop-blur-xl relative">
                <div className="absolute inset-0 bg-gradient-to-br from-pink-500/5 to-transparent opacity-30" />
                
                <table className="w-full text-left relative z-10">
                    <thead>
                        <tr className="border-b border-white/5">
                            <th className="px-8 py-6 text-[10px] font-black text-white/20 uppercase tracking-[0.2em]">Identificador</th>
                            <th className="px-8 py-6 text-[10px] font-black text-white/20 uppercase tracking-[0.2em]">Detalhes</th>
                            <th className="px-8 py-6 text-[10px] font-black text-white/20 uppercase tracking-[0.2em]">Status/Extra</th>
                            <th className="px-8 py-6 text-[10px] font-black text-white/20 uppercase tracking-[0.2em] text-right">Ações</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {activeTab === 'models' && data.models.map((item: any) => (
                            <tr key={item.id} className="group hover:bg-white/[0.02] transition-colors cursor-pointer" onClick={() => setSelectedModel(item)}>
                                <td className="px-8 py-6">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-white/40 group-hover:text-[var(--theme-primary)] transition-colors">
                                            <Box size={18} />
                                        </div>
                                        <div>
                                            <p className="text-sm font-black text-white uppercase">{item.model}</p>
                                            <p className="text-[10px] text-white/40 font-bold uppercase">{item.brand}</p>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-8 py-6">
                                    <span className="text-[10px] text-white/60 font-bold uppercase">{item.brand} • {item.power_hp} HP</span>
                                </td>
                                <td className="px-8 py-6">
                                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-[9px] font-black uppercase rounded-full border border-emerald-500/20">
                                        Homologado
                                    </span>
                                </td>
                                <td className="px-8 py-6 text-right">
                                    <button 
                                        onClick={(e) => handleDelete('models', item.id, e)}
                                        className="p-2 text-white/20 hover:text-rose-500 transition-colors"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}

                        {activeTab === 'sensors' && data.sensors.map((item: any) => (
                            <tr key={item.id} className="group hover:bg-white/[0.02] transition-colors">
                                <td className="px-8 py-6">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-white/40 group-hover:text-[var(--theme-primary)] transition-colors">
                                            <Cpu size={18} />
                                        </div>
                                        <p className="text-sm font-black text-white uppercase">{item.model_name}</p>
                                    </div>
                                </td>
                                <td className="px-8 py-6">
                                    <span className="text-[10px] text-white/60 font-bold uppercase">{item.manufacturer}</span>
                                </td>
                                <td className="px-8 py-6">
                                    <span className="text-[10px] text-white/40 font-black uppercase tracking-widest">{item.protocol}</span>
                                </td>
                                <td className="px-8 py-6 text-right">
                                    <button 
                                        onClick={(e) => handleDelete('sensors', item.id, e)}
                                        className="p-2 text-white/20 hover:text-rose-500 transition-colors"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}

                        {activeTab === 'variables' && data.variables.map((item: any) => (
                            <tr key={item.id} className="group hover:bg-white/[0.02] transition-colors">
                                <td className="px-8 py-6">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center text-white/40 group-hover:text-[var(--theme-primary)] transition-colors">
                                            <Activity size={18} />
                                        </div>
                                        <p className="text-sm font-black text-white uppercase">{item.name}</p>
                                    </div>
                                </td>
                                <td className="px-8 py-6">
                                    <span className="text-[10px] text-white/60 font-bold uppercase">{item.description}</span>
                                </td>
                                <td className="px-8 py-6">
                                    <span className="text-xs text-[var(--theme-primary)] font-black">{item.unit}</span>
                                </td>
                                <td className="px-8 py-6 text-right">
                                    <button 
                                        onClick={(e) => handleDelete('variables', item.id, e)}
                                        className="p-2 text-white/20 hover:text-rose-500 transition-colors"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                {loading && (
                    <div className="p-20 text-center text-white/20 font-black uppercase text-xs tracking-widest">
                        Carregando Catálogo Sarak...
                    </div>
                )}
            </div>

            {/* Model Detail Modal */}
            <AnimatePresence>
                {selectedModel && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-md">
                        <motion.div 
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-[#0a0a0a] border border-white/10 w-full max-w-2xl rounded-[3rem] overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.5)]"
                        >
                            <div className="p-12 space-y-8">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <div className="flex items-center gap-3 mb-4">
                                            <Shield className="text-emerald-400" size={16} />
                                            <span className="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Especificação de Fábrica</span>
                                        </div>
                                        <h2 className="text-3xl font-black text-white uppercase tracking-tighter">{selectedModel.model}</h2>
                                        <p className="text-white/40 font-bold uppercase text-[10px] tracking-widest">{selectedModel.brand} • {selectedModel.power_hp} HP</p>
                                    </div>
                                    <button onClick={() => setSelectedModel(null)} className="text-white/20 hover:text-white">
                                        <Plus size={24} className="rotate-45" />
                                    </button>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-6 bg-white/5 rounded-3xl border border-white/5">
                                        <p className="text-[9px] text-white/40 font-black uppercase mb-4 tracking-widest">Referência Manual</p>
                                        <div className="flex items-center gap-3">
                                            <Info size={16} className="text-[var(--theme-primary)]" />
                                            <span className="text-xs text-white font-bold">{selectedModel.spec_reference}</span>
                                        </div>
                                    </div>
                                    <div className="p-6 bg-white/5 rounded-3xl border border-white/5">
                                        <p className="text-[9px] text-white/40 font-black uppercase mb-4 tracking-widest">Certificação</p>
                                        <div className="flex items-center gap-3">
                                            <Zap size={16} className="text-amber-400" />
                                            <span className="text-xs text-white font-bold">IEC 60034-30-1</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <p className="text-[10px] text-white/40 font-black uppercase tracking-[0.2em]">Variáveis Monitoradas & Thresholds</p>
                                    <div className="space-y-2">
                                        {Object.entries(selectedModel.default_thresholds).map(([varId, thresholds]: any) => {
                                            const varName = data.variables.find((v:any) => v.id === varId)?.name || "Variável";
                                            const unit = data.variables.find((v:any) => v.id === varId)?.unit || "";
                                            return (
                                                <div key={varId} className="flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-2xl">
                                                    <div className="flex items-center gap-3">
                                                        <div className="p-2 bg-white/5 rounded-lg">
                                                            {varName.includes("Temp") ? <Thermometer size={14} className="text-amber-400" /> : <Gauge size={14} className="text-emerald-400" />}
                                                        </div>
                                                        <span className="text-xs font-bold text-white/80 uppercase">{varName}</span>
                                                    </div>
                                                    <div className="flex gap-4">
                                                        <div className="text-center">
                                                            <p className="text-[8px] text-white/20 font-black uppercase">Nominal</p>
                                                            <p className="text-[10px] text-white font-black">{thresholds.nominal}{unit}</p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-[8px] text-amber-400/40 font-black uppercase">Alerta</p>
                                                            <p className="text-[10px] text-amber-400 font-black">{thresholds.warning}{unit}</p>
                                                        </div>
                                                        <div className="text-center">
                                                            <p className="text-[8px] text-rose-500/40 font-black uppercase">Crítico</p>
                                                            <p className="text-[10px] text-rose-500 font-black">{thresholds.critical}{unit}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            {/* Sovereign Note */}
            <div className="p-6 bg-white/5 rounded-3xl border border-white/5 flex items-start gap-4">
                <Shield size={18} className="text-white/20 mt-1" />
                <p className="text-[10px] text-white/40 leading-relaxed uppercase font-medium">
                    <span className="text-white/60 font-black">Nota de Soberania:</span> As alterações feitas neste catálogo impactam diretamente o motor de regras do Gêmeo Digital e o provisionamento de novos ativos. Certifique-se de que os protocolos de sensores estejam configurados corretamente para evitar falhas de telemetria.
                </p>
            </div>
        </div>
    );
};

export default Catalogs;
