import React, { useState, useRef } from 'react';
import { Camera, Upload, CheckCircle, AlertCircle, Scan, History, FileText } from 'lucide-react';

const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

const Vision = () => {
    const [isScanning, setIsScanning] = useState(false);
    const [scanResult, setScanResult] = useState<any | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFile = async (file: File) => {
        if (!ACCEPTED_TYPES.includes(file.type)) {
            setError('Formato não suportado. Use JPG, PNG ou WEBP.');
            return;
        }

        setPreviewUrl(URL.createObjectURL(file));
        setError(null);
        setIsScanning(true);
        setScanResult(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/vision/scan', { method: 'POST', body: formData });
            if (res.ok) {
                setScanResult(await res.json());
            } else {
                const body = await res.json().catch(() => null);
                setError(body?.detail || 'Não foi possível processar a imagem.');
            }
        } catch (e) {
            setError('Falha de rede ao contatar o backend.');
        } finally {
            setIsScanning(false);
        }
    };

    const onFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleFile(file);
    };

    const onDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file) handleFile(file);
    };

    return (
        <div className="flex flex-col gap-6 p-6">
            <header className="flex justify-between items-center bg-theme-card border-theme p-6 rounded-theme">
                <div>
                    <h1 className="text-2xl font-black text-white uppercase tracking-tighter">Visão Computacional</h1>
                    <p className="text-xs text-white/40 uppercase font-bold tracking-widest mt-1">Extração de Dados via OCR — Motor WEG W22</p>
                </div>
                <div className="flex gap-3">
                    <button className="flex items-center gap-2 bg-white/5 hover:bg-white/10 text-white/60 border border-white/10 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all">
                        <History size={14} /> Histórico de Scans
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Zona de Upload / Visualização */}
                <div className="flex flex-col gap-6">
                    <div className="bg-theme-card border-theme p-6 rounded-theme flex flex-col gap-4">
                        <h3 className="text-xs font-black text-white/40 uppercase tracking-widest">Entrada de Imagem</h3>
                        
                        <div
                            onDrop={onDrop}
                            onDragOver={(e) => e.preventDefault()}
                            className="relative aspect-video bg-black/40 rounded-2xl border-2 border-dashed border-white/10 flex flex-col items-center justify-center gap-4 overflow-hidden group hover:border-[var(--theme-primary)] transition-all"
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept={ACCEPTED_TYPES.join(',')}
                                onChange={onFileInputChange}
                                className="hidden"
                            />
                            {isScanning && (
                                <div className="absolute inset-0 z-10 bg-[var(--theme-primary-bg)]/20 backdrop-blur-[2px] flex flex-col items-center justify-center">
                                    <div className="w-48 h-1 bg-white/10 rounded-full overflow-hidden relative">
                                        <div className="absolute inset-0 bg-[var(--theme-primary)] animate-[shimmer_2s_infinite]" style={{ width: '40%' }}></div>
                                    </div>
                                    <span className="mt-4 text-[10px] font-black text-[var(--theme-primary)] uppercase tracking-[0.2em] animate-pulse">Processando OCR...</span>
                                </div>
                            )}

                            {previewUrl ? (
                                <img
                                    src={previewUrl}
                                    alt="Placa Escaneada"
                                    className="w-full h-full object-cover opacity-80"
                                    loading="lazy"
                                />
                            ) : (
                                <>
                                    <div className="p-4 bg-white/5 rounded-full text-white/20 group-hover:text-[var(--theme-primary)] transition-colors">
                                        <Camera size={32} />
                                    </div>
                                    <div className="text-center">
                                        <p className="text-xs font-bold text-white/60">Arraste a foto da placa técnica</p>
                                        <p className="text-[10px] text-white/20 uppercase mt-1">Formatos: JPG, PNG, WEBP (Max 10MB)</p>
                                    </div>
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="mt-2 px-6 py-2 bg-white/5 border border-white/10 rounded-xl text-[10px] font-black text-white uppercase tracking-widest hover:bg-white/10 transition-all"
                                    >
                                        Selecionar Arquivo
                                    </button>
                                </>
                            )}
                        </div>

                        {error && (
                            <p className="text-xs text-rose-500 font-bold bg-rose-500/10 border border-rose-500/20 rounded-2xl p-4">
                                {error}
                            </p>
                        )}
                    </div>

                    <div className="bg-theme-card border-theme p-6 rounded-theme">
                        <div className="flex items-center gap-3 mb-4">
                            <AlertCircle size={18} className="text-[var(--theme-warning)]" />
                            <h4 className="text-xs font-black text-white uppercase tracking-tight">Instruções de Captura</h4>
                        </div>
                        <ul className="space-y-3">
                            {[
                                "Evite reflexos diretos na placa metálica.",
                                "Garanta que todos os campos da tabela estejam visíveis.",
                                "Mantenha a câmera paralela à superfície da placa."
                            ].map((text, i) => (
                                <li key={i} className="flex items-start gap-3 text-[11px] text-white/40 leading-relaxed">
                                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--theme-primary)] mt-1 shrink-0" />
                                    {text}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Resultados da Extração */}
                <div className="bg-theme-card border-theme p-8 rounded-theme flex flex-col gap-6 relative overflow-hidden">
                    {!scanResult && !isScanning && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/20 backdrop-blur-[4px] z-10">
                            <Scan size={48} className="text-white/5 mb-4" />
                            <p className="text-xs font-black text-white/20 uppercase tracking-widest">Aguardando Captura</p>
                        </div>
                    )}

                    <div className="flex justify-between items-start">
                        <div>
                            <h3 className="text-xs font-black text-white/40 uppercase tracking-widest mb-1">Dados Extraídos</h3>
                            <div className="flex items-center gap-2">
                                <CheckCircle size={14} className={scanResult ? "text-[var(--theme-success)]" : "text-white/10"} />
                                <span className="text-[10px] font-bold text-white/60 uppercase tracking-widest">Status: {scanResult ? "Sucesso" : "Pendente"}</span>
                            </div>
                        </div>
                        {scanResult && (
                            <div className="text-right">
                                <span className="text-[10px] font-black text-white/20 uppercase block mb-1">Confiança da IA</span>
                                <span className="text-xl font-black text-[var(--theme-success)]">{scanResult.confianca}%</span>
                            </div>
                        )}
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-4">
                        {scanResult ? (
                            Object.entries(scanResult).filter(([k]) => k !== 'confianca').map(([key, value]: any) => (
                                <div key={key} className="bg-black/20 border border-white/5 p-4 rounded-2xl group hover:border-[var(--theme-primary-border)] transition-all">
                                    <span className="text-[9px] font-black text-white/20 uppercase block mb-1">{key.replace('_', ' ')}</span>
                                    <span className="text-sm font-bold text-white group-hover:text-[var(--theme-primary)] transition-colors">{value}</span>
                                </div>
                            ))
                        ) : (
                            Array(8).fill(0).map((_, i) => (
                                <div key={i} className="h-16 bg-white/[0.02] border border-dashed border-white/5 rounded-2xl" />
                            ))
                        )}
                    </div>

                    {scanResult && (
                        <div className="mt-auto flex gap-3 pt-6 border-t border-white/5">
                            <button className="flex-1 bg-[var(--theme-primary)] text-black py-3 rounded-xl text-[10px] font-black uppercase tracking-widest hover:opacity-80 transition-all flex items-center justify-center gap-2">
                                <FileText size={14} /> Vincular ao Ativo
                            </button>
                            <button
                                onClick={() => { setScanResult(null); setPreviewUrl(null); setError(null); }}
                                className="px-6 py-3 bg-white/5 text-white/60 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-white/10 transition-all"
                            >
                                Novo Scan
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Vision;

