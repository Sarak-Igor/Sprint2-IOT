import React from 'react';
import { SarakTable, SarakStats } from '@sarak/lib-ui-core';
import { Box, Plus } from 'lucide-react';

const Assets = () => {
    return (
        <div className="flex flex-col gap-6 p-6">
            <div className="flex justify-between items-center bg-theme-card border-theme p-6 rounded-theme">
                <div>
                    <h2 className="text-2xl font-black text-white uppercase tracking-tighter">Gestão de Ativos</h2>
                    <p className="text-xs text-white/40 uppercase font-bold tracking-widest mt-1">Inventário Industrial e Especificações Técnicas</p>
                </div>
                <button className="flex items-center gap-2 bg-[var(--theme-primary)] hover:opacity-80 text-black px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all">
                    <Plus size={14} /> Novo Ativo
                </button>
            </div>

            <SarakStats
                endpoint="assets/stats"
                mapping={{
                    total: "Ativos Totais",
                    alerts: "Alertas de Serviço",
                    health_score: "Saúde Geral (%)"
                }}
            />

            <div className="bg-theme-card border-theme p-6 rounded-theme">
                <SarakTable
                    endpoint="assets"
                    label="Inventário de Equipamentos"
                    mapping={{
                        tag: "TAG Ativo",
                        type: "Tipo",
                        model: "Modelo",
                        health: "Saúde (%)",
                        status: "Status"
                    }}
                    role="primary"
                />
            </div>
        </div>
    );
};

export default Assets;

