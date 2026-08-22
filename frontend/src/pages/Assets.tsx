import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SarakTable } from '@sarak/lib-ui-core';
import { Box, MapPin, Trash2, Plus, Sparkles } from 'lucide-react';

const EMPTY_FORM = { name: '', location: '', description: '' };

const Assets = () => {
    const [assets, setAssets] = useState<any[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [form, setForm] = useState(EMPTY_FORM);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchAssets = async () => {
        try {
            const res = await fetch('/api/assets/dashboard');
            if (res.ok) setAssets(await res.json());
        } catch (e) {}
    };

    useEffect(() => {
        fetchAssets();
    }, []);

    const handleDelete = async (id: string) => {
        if (!confirm("Remover este registro de provisionamento?")) return;
        try {
            const res = await fetch(`/api/assets/active/${id}`, { method: 'DELETE' });
            if (res.ok) fetchAssets();
        } catch (e) {}
    };

    const openModal = () => {
        setForm(EMPTY_FORM);
        setError(null);
        setIsModalOpen(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        try {
            const res = await fetch('/api/assets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form),
            });
            if (res.ok) {
                setIsModalOpen(false);
                fetchAssets();
            } else {
                const body = await res.json().catch(() => null);
                setError(body?.detail || 'Não foi possível cadastrar o ativo.');
            }
        } catch (e) {
            setError('Falha de rede ao contatar o backend.');
        } finally {
            setSubmitting(false);
        }
    };

    const columns = [
        { header: 'Tag do Ativo', accessor: 'name' },
        { header: 'Localização', accessor: 'location' },
        { header: 'Modelo Industrial', render: (row: any) => row.motor_model?.model || 'Desconhecido' },
        { header: 'Status', render: (row: any) => (
            <span className="text-[10px] font-black uppercase text-emerald-400 bg-emerald-400/10 px-3 py-1 rounded-full">
                {row.status}
            </span>
        )},
        { header: 'Ações', render: (row: any) => (
            <div className="flex gap-2">
                <button onClick={() => handleDelete(row.id)} className="p-2 hover:bg-red-500/20 text-red-500 rounded-lg transition-colors">
                    <Trash2 size={16} />
                </button>
            </div>
        )}
    ];

    return (
        <div className="p-10 space-y-8 max-w-7xl mx-auto w-full">
            <header className="flex justify-between items-center bg-theme-card border-theme p-8 rounded-2xl shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-10 opacity-[0.02]">
                    <Box size={120} />
                </div>
                <div className="relative z-10">
                    <h2 className="text-3xl font-black text-white uppercase tracking-tighter">Setor de Provisionamento</h2>
                    <p className="text-[10px] text-white/40 uppercase font-black tracking-[0.2em] mt-2">Log de Ativos e Inventário de Hardware</p>
                </div>
                <button
                    onClick={openModal}
                    className="relative z-10 flex items-center gap-2 bg-[var(--theme-primary)] text-black font-black uppercase text-xs tracking-widest px-6 py-4 rounded-2xl hover:opacity-90 transition-opacity"
                >
                    <Plus size={16} /> Novo Ativo
                </button>
            </header>

            <div className="bg-theme-card border-theme rounded-2xl overflow-hidden shadow-2xl">
                <SarakTable
                    data={assets}
                    columns={columns}
                    emptyMessage="Nenhum ativo provisionado no momento."
                />
            </div>

            <AnimatePresence>
                {isModalOpen && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-8 bg-black/80 backdrop-blur-md">
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-[#0a0a0a] border border-white/10 w-full max-w-lg rounded-[3rem] overflow-hidden shadow-[0_0_100px_rgba(0,0,0,0.5)]"
                        >
                            <form onSubmit={handleSubmit} className="p-12 space-y-8">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <div className="flex items-center gap-3 mb-4">
                                            <Sparkles className="text-[var(--theme-primary)]" size={16} />
                                            <span className="text-[10px] font-black text-[var(--theme-primary)] uppercase tracking-widest">Cadastro Assistido por IA</span>
                                        </div>
                                        <h2 className="text-2xl font-black text-white uppercase tracking-tighter">Novo Ativo</h2>
                                    </div>
                                    <button type="button" onClick={() => setIsModalOpen(false)} className="text-white/20 hover:text-white">
                                        <Plus size={24} className="rotate-45" />
                                    </button>
                                </div>

                                <div className="space-y-6">
                                    <div className="flex flex-col gap-3">
                                        <label className="text-[11px] font-black text-white/30 uppercase tracking-[0.2em] ml-2">Tag de Identificação</label>
                                        <input
                                            required
                                            value={form.name}
                                            onChange={(e) => setForm({ ...form, name: e.target.value })}
                                            className="bg-black/40 border border-white/5 p-5 rounded-2xl text-white font-bold outline-none focus:border-[var(--theme-primary)] focus:bg-black/60 transition-all placeholder:text-white/10"
                                            placeholder="Ex: W22_MOTOR_004"
                                        />
                                    </div>
                                    <div className="flex flex-col gap-3">
                                        <label className="text-[11px] font-black text-white/30 uppercase tracking-[0.2em] ml-2">Localização</label>
                                        <div className="relative group">
                                            <MapPin className="absolute left-5 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-[var(--theme-primary)] transition-colors" size={18} />
                                            <input
                                                required
                                                value={form.location}
                                                onChange={(e) => setForm({ ...form, location: e.target.value })}
                                                className="w-full bg-black/40 border border-white/5 p-5 pl-14 rounded-2xl text-white font-bold outline-none focus:border-[var(--theme-primary)] focus:bg-black/60 transition-all placeholder:text-white/10"
                                                placeholder="Setor / Ala / Pavimento"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex flex-col gap-3">
                                        <label className="text-[11px] font-black text-white/30 uppercase tracking-[0.2em] ml-2">Marca, modelo ou descrição livre</label>
                                        <textarea
                                            required
                                            minLength={3}
                                            maxLength={500}
                                            rows={3}
                                            value={form.description}
                                            onChange={(e) => setForm({ ...form, description: e.target.value })}
                                            className="bg-black/40 border border-white/5 p-5 rounded-2xl text-white font-bold outline-none focus:border-[var(--theme-primary)] focus:bg-black/60 transition-all placeholder:text-white/10 resize-none"
                                            placeholder="Ex: WEG W22 100cv trifásico IP55"
                                        />
                                        <p className="text-[10px] text-white/30 ml-2">
                                            A IA deduz potência, RPM nominal e grau de proteção a partir desta descrição.
                                        </p>
                                    </div>
                                </div>

                                {error && (
                                    <p className="text-xs text-rose-500 font-bold bg-rose-500/10 border border-rose-500/20 rounded-2xl p-4">
                                        {error}
                                    </p>
                                )}

                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="w-full flex items-center justify-center gap-2 bg-[var(--theme-primary)] text-black font-black uppercase text-xs tracking-widest px-6 py-5 rounded-2xl hover:opacity-90 transition-opacity disabled:opacity-40"
                                >
                                    {submitting ? 'Consultando IA...' : 'Cadastrar com IA'}
                                </button>
                            </form>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Assets;
