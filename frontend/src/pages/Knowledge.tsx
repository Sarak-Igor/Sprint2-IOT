import React, { useState, useEffect, useRef } from 'react';
import { Search, BookOpen, FileText, Download, ExternalLink, Info, Book, Loader2, Sparkles, Upload, Send } from 'lucide-react';

interface Manual {
    manual_id: string;
    filename: string;
    paginas: number;
    chunks_indexados: number;
    tamanho_bytes: number;
    download_url: string;
}

const formatBytes = (bytes: number): string => {
    if (bytes <= 0) return '—';
    const units = ['B', 'KB', 'MB', 'GB'];
    let value = bytes;
    let unitIndex = 0;
    while (value >= 1024 && unitIndex < units.length - 1) {
        value /= 1024;
        unitIndex += 1;
    }
    return `${value.toFixed(1)} ${units[unitIndex]}`;
};

interface SourceCitation {
    manual: string;
    pagina: number;
    trecho: string;
}

interface AskResult {
    resposta: string;
    fontes: SourceCitation[];
}

const Knowledge = () => {
    const [search, setSearch] = useState('');
    const [manuals, setManuals] = useState<Manual[]>([]);
    const [loading, setLoading] = useState(true);

    const [question, setQuestion] = useState('');
    const [askLoading, setAskLoading] = useState(false);
    const [askResult, setAskResult] = useState<AskResult | null>(null);
    const [askError, setAskError] = useState<string | null>(null);

    const [uploading, setUploading] = useState(false);
    const [uploadMessage, setUploadMessage] = useState<string | null>(null);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const fetchManuals = async () => {
            try {
                const response = await fetch('/api/knowledge/manuals');
                if (response.ok) {
                    const data = await response.json();
                    setManuals(data);
                }
            } catch (error) {
                console.error("[ERRO] Falha ao carregar manuais:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchManuals();
    }, []);

    const handleAsk = async (e: React.FormEvent) => {
        e.preventDefault();
        if (question.trim().length < 3) return;

        setAskLoading(true);
        setAskError(null);
        setAskResult(null);

        try {
            const res = await fetch('/api/knowledge/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pergunta: question }),
            });
            if (res.ok) {
                setAskResult(await res.json());
            } else {
                const body = await res.json().catch(() => null);
                setAskError(body?.detail || 'Não foi possível obter resposta.');
            }
        } catch (e) {
            setAskError('Falha de rede ao contatar o backend.');
        } finally {
            setAskLoading(false);
        }
    };

    const handleUploadManual = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        setUploadError(null);
        setUploadMessage(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/api/knowledge/ingest', { method: 'POST', body: formData });
            if (res.ok) {
                const body = await res.json();
                setUploadMessage(`"${body.filename}" indexado (${body.chunks_indexados} trechos, ${body.paginas} páginas).`);
            } else {
                const body = await res.json().catch(() => null);
                setUploadError(body?.detail || 'Não foi possível indexar o manual.');
            }
        } catch (e) {
            setUploadError('Falha de rede ao contatar o backend.');
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const glossary = [
        { term: 'Carcaca', definition: 'Estrutura externa do motor que suporta o estator e protege os componentes internos.' },
        { term: 'IP55', definition: 'Grau de proteção contra entrada de poeira e jatos de água de qualquer direção.' },
        { term: 'Classe F', definition: 'Limite de temperatura de isolamento de 155°C, garantindo durabilidade térmica.' },
        { term: 'Fator de Serviço (FS)', definition: 'Multiplicador que indica a sobrecarga permissível que o motor pode suportar continuamente.' },
        { term: 'Escorregamento', definition: 'Diferença entre a velocidade síncrona e a velocidade real de rotação do motor.' }
    ];

    const handleDownload = (url: string, filename: string, e?: React.MouseEvent) => {
        if (e) e.stopPropagation();
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.target = "_blank";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleOpen = (url: string) => {
        window.open(url, '_blank');
    };

    return (
        <div className="flex flex-col gap-10 p-10 max-w-7xl mx-auto w-full">
            {/* Header com Busca */}
            <div className="text-center flex flex-col items-center gap-6">
                <header>
                    <h1 className="text-4xl font-black text-white tracking-tighter uppercase">Knowledge Base</h1>
                    <p className="text-white/40 max-w-md mx-auto mt-2 font-medium">Repositório soberano de inteligência técnica e documentação industrial.</p>
                </header>
                
                <div className="relative w-full max-w-2xl group">
                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-[var(--theme-primary)] transition-colors" size={20} />
                    <input 
                        type="text" 
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Pesquise por manuais, normas ou termos técnicos..." 
                        className="w-full bg-theme-card border-theme py-5 pl-16 pr-6 rounded-2xl text-lg text-white outline-none focus:border-[var(--theme-primary)] transition-all shadow-2xl"
                    />
                </div>
            </div>

            {/* Assistente de Conhecimento (RAG) */}
            <div className="bg-theme-card border-theme p-8 rounded-theme flex flex-col gap-6">
                <div className="flex items-center gap-3">
                    <Sparkles size={20} className="text-[var(--theme-primary)]" />
                    <h2 className="text-sm font-black text-white uppercase tracking-widest">Assistente de Conhecimento</h2>
                </div>

                <form onSubmit={handleAsk} className="flex gap-3">
                    <input
                        type="text"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Pergunte algo sobre os manuais indexados..."
                        className="flex-1 bg-black/20 border border-white/10 py-4 px-6 rounded-2xl text-white outline-none focus:border-[var(--theme-primary)] transition-all"
                    />
                    <button
                        type="submit"
                        disabled={askLoading || question.trim().length < 3}
                        className="flex items-center gap-2 bg-[var(--theme-primary)] text-black font-black uppercase text-xs tracking-widest px-6 py-4 rounded-2xl hover:opacity-90 transition-opacity disabled:opacity-40"
                    >
                        {askLoading ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
                        Perguntar
                    </button>
                </form>

                {askError && (
                    <p className="text-xs text-rose-500 font-bold bg-rose-500/10 border border-rose-500/20 rounded-2xl p-4">
                        {askError}
                    </p>
                )}

                {askResult && (
                    <div className="bg-black/20 border border-white/5 rounded-2xl p-6 flex flex-col gap-4">
                        <p className="text-sm text-white leading-relaxed">{askResult.resposta}</p>
                        {askResult.fontes.length > 0 && (
                            <div className="flex flex-col gap-2 pt-4 border-t border-white/5">
                                <span className="text-[10px] font-black text-white/20 uppercase tracking-widest">Fontes</span>
                                {askResult.fontes.map((fonte, i) => (
                                    <span key={i} className="text-[11px] text-white/40">
                                        {fonte.manual} — página {fonte.pagina}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                {/* Coluna de Manuais */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <FileText size={20} className="text-[var(--theme-primary)]" />
                            <h2 className="text-sm font-black text-white uppercase tracking-widest">Documentação Técnica</h2>
                        </div>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="application/pdf"
                            onChange={handleUploadManual}
                            className="hidden"
                        />
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            disabled={uploading}
                            className="flex items-center gap-2 bg-white/5 hover:bg-white/10 text-white/60 border border-white/10 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all disabled:opacity-40"
                        >
                            {uploading ? <Loader2 className="animate-spin" size={14} /> : <Upload size={14} />}
                            Novo Manual
                        </button>
                    </div>

                    {(uploadMessage || uploadError) && (
                        <p className={`text-[11px] font-bold p-4 rounded-2xl border ${uploadError ? 'text-rose-500 bg-rose-500/10 border-rose-500/20' : 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20'}`}>
                            {uploadError || uploadMessage}
                        </p>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {loading ? (
                            <div className="col-span-2 flex items-center justify-center py-20 bg-theme-card border-theme rounded-theme">
                                <Loader2 className="animate-spin text-[var(--theme-primary)]" size={32} />
                            </div>
                        ) : manuals.length > 0 ? (
                            manuals.filter(m => m.filename.toLowerCase().includes(search.toLowerCase())).map((doc) => (
                                <div
                                    key={doc.manual_id}
                                    onClick={() => handleOpen(doc.download_url)}
                                    className="bg-theme-card border-theme p-6 rounded-theme hover:bg-white/[0.04] transition-all group cursor-pointer border-l-2 border-l-transparent hover:border-l-[var(--theme-primary)]"
                                >
                                    <div className="flex justify-between items-start mb-6">
                                        <div className="p-3 bg-white/5 rounded-xl text-white/40 group-hover:text-[var(--theme-primary)] transition-colors">
                                            <BookOpen size={24} />
                                        </div>
                                        <button
                                            onClick={(e) => handleDownload(doc.download_url, doc.filename, e)}
                                            className="p-2 bg-white/5 rounded-lg text-white/20 hover:text-white transition-colors"
                                        >
                                            <Download size={16} />
                                        </button>
                                    </div>
                                    <h4 className="text-base font-black text-white uppercase tracking-tight mb-4 leading-tight">{doc.filename}</h4>
                                    <div className="flex items-center justify-between mt-auto pt-4 border-t border-white/5">
                                        <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">
                                            {formatBytes(doc.tamanho_bytes)} · {doc.paginas} pág. · {doc.chunks_indexados} trechos
                                        </span>
                                        <span className="text-[10px] font-black text-[var(--theme-primary)] uppercase tracking-widest flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            Abrir <ExternalLink size={10} />
                                        </span>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="col-span-2 text-center py-20 text-white/20 font-black uppercase tracking-widest">
                                Nenhum manual encontrado
                            </div>
                        )}
                    </div>
                </div>

                {/* Coluna de Glossário */}
                <div className="flex flex-col gap-6">
                    <div className="flex items-center gap-3">
                        <Book size={20} className="text-[var(--theme-secondary)]" />
                        <h2 className="text-sm font-black text-white uppercase tracking-widest">Glossário Industrial</h2>
                    </div>

                    <div className="bg-theme-card border-theme p-8 rounded-theme flex flex-col gap-6">
                        {glossary.map((item, i) => (
                            <div key={i} className="flex flex-col gap-2 group">
                                <div className="flex items-center gap-2">
                                    <Info size={12} className="text-[var(--theme-primary)] opacity-40 group-hover:opacity-100" />
                                    <h5 className="text-[11px] font-black text-white uppercase tracking-wider">{item.term}</h5>
                                </div>
                                <p className="text-[11px] text-white/40 leading-relaxed group-hover:text-white/60 transition-colors">
                                    {item.definition}
                                </p>
                                {i !== glossary.length - 1 && <div className="h-[1px] bg-white/5 mt-4" />}
                            </div>
                        ))}
                        <button className="mt-4 w-full py-3 bg-white/5 text-[10px] font-black text-white/40 uppercase tracking-widest rounded-xl hover:bg-white/10 transition-all">
                            Ver Glossário Completo
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Knowledge;

