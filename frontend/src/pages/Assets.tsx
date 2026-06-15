import React, { useState, useEffect } from 'react';
import { SarakTable } from '@sarak/lib-ui-core';
import { Box, Settings, MapPin, Zap, Trash2, ExternalLink } from 'lucide-react';

const Assets = () => {
    const [assets, setAssets] = useState<any[]>([]);

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
            </header>

            <div className="bg-theme-card border-theme rounded-2xl overflow-hidden shadow-2xl">
                <SarakTable 
                    data={assets}
                    columns={columns}
                    emptyMessage="Nenhum ativo provisionado no momento."
                />
            </div>
        </div>
    );
};

export default Assets;
