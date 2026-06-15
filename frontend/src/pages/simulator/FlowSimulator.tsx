import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { 
    Background, 
    Controls, 
    useNodesState, 
    useEdgesState,
    MarkerType,
    Node,
    Edge
} from 'reactflow';
import 'reactflow/dist/style.css';
import { motion } from 'framer-motion';
import { Activity, RefreshCcw, Info, Play, Pause } from 'lucide-react';

import { SourceNode, BrokerNode, CoreNode, DBNode, StreamingNode, UINode, TelegramNode } from './nodes/CustomNodes';
import { AnimatedEdge } from './edges/AnimatedEdge';

const nodeTypes = {
    source: SourceNode,
    broker: BrokerNode,
    core: CoreNode,
    database: DBNode,
    streaming: StreamingNode,
    ui: UINode,
    telegram: TelegramNode
};

const edgeTypes = {
    animated: AnimatedEdge
};

const initialNodes: Node[] = [
    { id: 'n1', type: 'source', position: { x: 50, y: 150 }, data: { label: 'Motor Sensor', active: false, interval: 5 } },
    { id: 'n2', type: 'broker', position: { x: 300, y: 150 }, data: { active: false } },
    { id: 'n3', type: 'core', position: { x: 550, y: 150 }, data: { active: false, processing: false } },
    { id: 'n4', type: 'database', position: { x: 550, y: 300 }, data: { active: false } },
    { id: 'n5', type: 'streaming', position: { x: 800, y: 150 }, data: { active: false } },
    { id: 'n6', type: 'ui', position: { x: 1050, y: 150 }, data: { active: false } },
    { id: 'n7', type: 'telegram', position: { x: 1300, y: 150 }, data: { active: false, alertType: null } },
];

const initialEdges: Edge[] = [
    { id: 'e1-2', source: 'n1', target: 'n2', type: 'animated', data: { color: '#3b82f6' } },
    { id: 'e2-3', source: 'n2', target: 'n3', type: 'animated', data: { color: '#f59e0b' } },
    { id: 'e3-4', source: 'n3', sourceHandle: 'db', target: 'n4', type: 'animated', data: { color: '#8b5cf6' } },
    { id: 'e3-5', source: 'n3', target: 'n5', type: 'animated', data: { color: '#10b981' } },
    { id: 'e5-6', source: 'n5', target: 'n6', type: 'animated', data: { color: '#ec4899' } },
    { id: 'e6-7', source: 'n6', target: 'n7', type: 'animated', data: { color: '#38bdf8' } },
];

const FlowSimulator = () => {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
    const [lastEvent, setLastEvent] = useState<any>(null);
    const [interval, setIntervalVal] = useState(5);
    const [isPaused, setIsPaused] = useState(false);

    const triggerFlow = useCallback(async (eventData?: any) => {
        // Verifica se é uma anomalia baseada num limite visual (ex: > 90)
        let alertType = null;
        if (eventData && eventData.value !== undefined) {
            if (eventData.value >= 90) alertType = 'PERIGO';
            else if (eventData.value >= 75) alertType = 'ATENÇÃO';
        }

        // Sequência de animação
        const steps = [
            { node: 'n1', edge: 'e1-2' },
            { node: 'n2', edge: 'e2-3' },
            { node: 'n3', edge: ['e3-4', 'e3-5'], extra: { processing: true } },
            { node: ['n4', 'n5'], edge: 'e5-6' },
            { node: 'n6', edge: alertType ? 'e6-7' : null },
            { node: alertType ? 'n7' : null, extra: { alertType } }
        ].filter(s => s.node !== null);

        for (const step of steps) {
            // Ativa Nodes
            setNodes(nds => nds.map(n => {
                const isActive = Array.isArray(step.node) ? step.node.includes(n.id) : n.id === step.node;
                if (isActive) {
                    return { ...n, data: { ...n.data, active: true, ...(step.extra || {}) } };
                }
                return n;
            }));

            // Ativa Edges
            if (step.edge) {
                setEdges(eds => eds.map(e => {
                    const isActive = Array.isArray(step.edge) ? step.edge.includes(e.id) : e.id === step.edge;
                    if (isActive) {
                        return { ...e, data: { ...e.data, active: true } };
                    }
                    return e;
                }));
            }

            await new Promise(r => setTimeout(r, 600));

            // Desativa Edges para o próximo passo
            if (step.edge) {
                setEdges(eds => eds.map(e => ({ ...e, data: { ...e.data, active: false } })));
            }
            
            // Pequeno delay entre passos
            await new Promise(r => setTimeout(r, 100));
        }

        // Reset final
        setTimeout(() => {
            setNodes(nds => nds.map(n => ({ ...n, data: { ...n.data, active: false, processing: false, alertType: null } })));
        }, 1000);
    }, [setNodes, setEdges]);

    useEffect(() => {
        // Fetch Config
        const fetchConfig = async () => {
            try {
                const res = await fetch('/api/config');
                if (res.ok) {
                    const data = await res.json();
                    setIntervalVal(data.interval);
                    setNodes(nds => nds.map(n => n.id === 'n1' ? { ...n, data: { ...n.data, interval: data.interval } } : n));
                }
            } catch (e) {}
        };
        fetchConfig();

        // WebSocket Integration
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/ws/telemetry`;
        const ws = new WebSocket(wsUrl);

        ws.onmessage = (event) => {
            if (isPaused) return;
            try {
                const data = JSON.parse(event.data);
                setLastEvent(data);
                triggerFlow(data);
            } catch (e) {}
        };

        return () => ws.close();
    }, [triggerFlow, setNodes]);

    return (
        <div className="h-full w-full bg-[#020617] flex flex-col overflow-hidden">
            <div className="px-8 py-6 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Activity className="text-blue-500" />
                        Forzy Flow Vision
                        <span className="px-2 py-1 rounded bg-blue-500/10 text-blue-400 text-xs font-mono border border-blue-500/20">
                            DEMO MODE
                        </span>
                    </h1>
                    <p className="text-slate-400 text-sm mt-1">
                        Visualização em tempo real do pipeline de dados industrial.
                    </p>
                </div>
                
                <div className="flex items-center gap-4">
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Status Visual</span>
                        <span className={`text-xs font-mono px-2 py-1 rounded border ${isPaused ? 'text-amber-400 bg-amber-500/10 border-amber-500/20' : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'}`}>
                            {isPaused ? 'PAUSED' : 'LIVE STREAMING'}
                        </span>
                    </div>
                    
                    <div className="flex items-center gap-2 bg-slate-800/50 p-1 rounded-xl border border-slate-700">
                        <button 
                            onClick={() => setIsPaused(!isPaused)}
                            className={`p-2.5 rounded-lg transition-all ${isPaused ? 'bg-amber-500 text-white shadow-lg shadow-amber-900/20' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'}`}
                            title={isPaused ? "Retomar Fluxo" : "Pausar Visualização"}
                        >
                            {isPaused ? <Play size={18} fill="currentColor" /> : <Pause size={18} fill="currentColor" />}
                        </button>
                        
                        <button 
                            onClick={() => triggerFlow()}
                            disabled={isPaused}
                            className={`p-2.5 rounded-lg transition-all ${isPaused ? 'opacity-30 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20'}`}
                            title="Disparar Pulso Manual"
                        >
                            <RefreshCcw size={18} />
                        </button>
                    </div>
                </div>
            </div>

            <div className="flex-1 relative">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={nodeTypes}
                    edgeTypes={edgeTypes}
                    fitView
                    className="bg-slate-950"
                >
                    <Background color="#1e293b" gap={20} />
                    <Controls className="!bg-slate-900 !border-slate-700 !fill-white" />
                </ReactFlow>

                {/* Overlay Info */}
                <div className="absolute bottom-6 left-6 p-4 rounded-2xl bg-slate-900/80 backdrop-blur-lg border border-slate-800 max-w-xs shadow-2xl">
                    <div className="flex items-start gap-3">
                        <Info className="text-blue-400 mt-1" size={18} />
                        <div>
                            <h4 className="text-sm font-bold text-white">Como funciona?</h4>
                            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                                Este simulador reflete o caminho físico e digital que o dado percorre. 
                                Cada "pulso" visual é acionado por uma mensagem real vinda do WebSocket, 
                                respeitando o intervalo de amostragem definido para o ativo.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FlowSimulator;
