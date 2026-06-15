import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { 
    Cpu, 
    Server, 
    Database, 
    Wifi, 
    Layout, 
    Settings,
    Activity,
    Zap,
    Send
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const NodeWrapper = ({ children, label, icon: Icon, color, active }: any) => (
    <div className={`
        relative px-4 py-3 rounded-xl border-2 transition-all duration-500
        ${active ? 'scale-105 shadow-[0_0_20px_rgba(var(--node-color),0.4)]' : 'scale-100 shadow-xl'}
        bg-slate-900/90 backdrop-blur-md border-slate-700/50
    `} style={{ '--node-color': color } as any}>
        <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg bg-opacity-20`} style={{ backgroundColor: `rgba(${color}, 0.2)`, color: `rgb(${color})` }}>
                <Icon size={20} className={active ? 'animate-pulse' : ''} />
            </div>
            <div>
                <p className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">{label}</p>
                <div className="flex items-center gap-2">
                    <div className="text-sm font-semibold text-white">{children}</div>
                    {active && (
                        <motion.div 
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="w-2 h-2 rounded-full" 
                            style={{ backgroundColor: `rgb(${color})` }}
                        />
                    )}
                </div>
            </div>
        </div>
        
        {/* Glow effect when active */}
        <AnimatePresence>
            {active && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 rounded-xl pointer-events-none"
                    style={{ 
                        boxShadow: `inset 0 0 15px rgba(${color}, 0.3), 0 0 20px rgba(${color}, 0.2)` 
                    }}
                />
            )}
        </AnimatePresence>
    </div>
);

export const SourceNode = memo(({ data }: any) => (
    <div className="relative">
        <NodeWrapper label="Data Source" icon={Cpu} color="59, 130, 246" active={data.active}>
            {data.label || 'IoT Device / Sim'}
            <p className="text-[9px] text-blue-400 mt-1">
                Interval: {data.interval}s
            </p>
        </NodeWrapper>
        <Handle type="source" position={Position.Right} style={{ background: '#3b82f6' }} />
    </div>
));

export const BrokerNode = memo(({ data }: any) => (
    <div className="relative">
        <Handle type="target" position={Position.Left} style={{ background: '#3b82f6' }} />
        <NodeWrapper label="Message Broker" icon={Zap} color="245, 158, 11" active={data.active}>
            MQTT Mosquitto
        </NodeWrapper>
        <Handle type="source" position={Position.Right} style={{ background: '#f59e0b' }} />
    </div>
));

export const CoreNode = memo(({ data }: any) => (
    <div className="relative">
        <Handle type="target" position={Position.Left} style={{ background: '#f59e0b' }} />
        <NodeWrapper label="Backend Engine" icon={Server} color="16, 185, 129" active={data.active}>
            FastAPI Core
            <p className="text-[9px] text-emerald-400 mt-1">
                {data.processing ? 'Processing...' : 'Idle'}
            </p>
        </NodeWrapper>
        <Handle type="source" position={Position.Right} style={{ background: '#10b981' }} />
        <Handle type="source" position={Position.Bottom} id="db" style={{ background: '#8b5cf6' }} />
    </div>
));

export const DBNode = memo(({ data }: any) => (
    <div className="relative">
        <Handle type="target" position={Position.Top} style={{ background: '#8b5cf6' }} />
        <NodeWrapper label="Storage" icon={Database} color="139, 92, 246" active={data.active}>
            PostgreSQL (Neon)
        </NodeWrapper>
    </div>
));

export const StreamingNode = memo(({ data }: any) => (
    <div className="relative">
        <Handle type="target" position={Position.Left} style={{ background: '#10b981' }} />
        <NodeWrapper label="Live Stream" icon={Wifi} color="236, 72, 153" active={data.active}>
            WebSocket Gateway
        </NodeWrapper>
        <Handle type="source" position={Position.Right} style={{ background: '#ec4899' }} />
    </div>
));

export const UINode = memo(({ data }: any) => (
    <div className="relative">
        <Handle type="target" position={Position.Left} style={{ background: '#ec4899' }} />
        <NodeWrapper label="Interface" icon={Layout} color="244, 63, 94" active={data.active}>
            Digital Twin Dashboard
        </NodeWrapper>
        <Handle type="source" position={Position.Right} style={{ background: '#38bdf8' }} />
    </div>
));

export const TelegramNode = memo(({ data }: any) => (
    <div className="relative">
        <Handle type="target" position={Position.Left} style={{ background: '#38bdf8' }} />
        <NodeWrapper label="Notification" icon={Send} color="56, 189, 248" active={data.active}>
            Telegram Bot
            <p className="text-[9px] text-sky-400 mt-1">
                {data.alertType ? `Alert: ${data.alertType}` : 'Monitoring...'}
            </p>
        </NodeWrapper>
    </div>
));
