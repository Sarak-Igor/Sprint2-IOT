import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Loader2, User, Sparkles } from 'lucide-react';

interface SourceCitation {
    manual: string;
    pagina: number;
    trecho: string;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    texto: string;
    fontes?: SourceCitation[];
}

const Agent = () => {
    const [sessionId] = useState<string>(() => crypto.randomUUID());
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        const mensagem = input.trim();
        if (!mensagem || loading) return;

        setMessages((prev) => [...prev, { role: 'user', texto: mensagem }]);
        setInput('');
        setLoading(true);
        setError(null);

        try {
            const res = await fetch('/api/agent/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, mensagem }),
            });
            if (res.ok) {
                const body = await res.json();
                setMessages((prev) => [
                    ...prev,
                    { role: 'assistant', texto: body.resposta, fontes: body.fontes },
                ]);
            } else {
                const body = await res.json().catch(() => null);
                setError(body?.detail || 'Não foi possível obter resposta do agente.');
            }
        } catch (e) {
            setError('Falha de rede ao contatar o backend.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col gap-8 p-10 max-w-4xl mx-auto w-full h-full">
            <header className="text-center flex flex-col items-center gap-2">
                <div className="flex items-center gap-3">
                    <Bot size={28} className="text-[var(--theme-primary)]" />
                    <h1 className="text-4xl font-black text-white tracking-tighter uppercase">Agente Forzy</h1>
                </div>
                <p className="text-white/40 max-w-md mx-auto font-medium">
                    Converse com o assistente de IA — consulta a base de manuais técnicos quando necessário.
                </p>
            </header>

            <div className="bg-theme-card border-theme rounded-theme flex flex-col gap-6 p-8 flex-1 min-h-[50vh]">
                <div className="flex flex-col gap-6 overflow-y-auto flex-1">
                    {messages.length === 0 && (
                        <div className="flex-1 flex items-center justify-center text-white/20 font-black uppercase tracking-widest text-sm text-center py-20">
                            Pergunte algo sobre os manuais técnicos indexados
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                        >
                            <div className="p-2 h-fit bg-white/5 rounded-xl text-white/40">
                                {msg.role === 'user' ? <User size={16} /> : <Sparkles size={16} className="text-[var(--theme-primary)]" />}
                            </div>
                            <div
                                className={`max-w-[80%] rounded-2xl p-4 flex flex-col gap-3 ${
                                    msg.role === 'user'
                                        ? 'bg-[var(--theme-primary)] text-black font-bold'
                                        : 'bg-black/20 border border-white/5 text-white'
                                }`}
                            >
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.texto}</p>
                                {msg.fontes && msg.fontes.length > 0 && (
                                    <div className="flex flex-col gap-1 pt-3 border-t border-white/10">
                                        <span className="text-[10px] font-black text-white/40 uppercase tracking-widest">Fontes</span>
                                        {msg.fontes.map((fonte, j) => (
                                            <span key={j} className="text-[11px] text-white/50">
                                                {fonte.manual} — página {fonte.pagina}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div className="flex gap-3">
                            <div className="p-2 h-fit bg-white/5 rounded-xl text-white/40">
                                <Sparkles size={16} className="text-[var(--theme-primary)]" />
                            </div>
                            <div className="bg-black/20 border border-white/5 rounded-2xl p-4">
                                <Loader2 className="animate-spin text-white/40" size={16} />
                            </div>
                        </div>
                    )}

                    <div ref={bottomRef} />
                </div>

                {error && (
                    <p className="text-xs text-rose-500 font-bold bg-rose-500/10 border border-rose-500/20 rounded-2xl p-4">
                        {error}
                    </p>
                )}

                <form onSubmit={handleSend} className="flex gap-3">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Pergunte sobre manuais e especificações técnicas..."
                        maxLength={1000}
                        className="flex-1 bg-black/20 border border-white/10 py-4 px-6 rounded-2xl text-white outline-none focus:border-[var(--theme-primary)] transition-all"
                    />
                    <button
                        type="submit"
                        disabled={loading || input.trim().length === 0}
                        className="flex items-center gap-2 bg-[var(--theme-primary)] text-black font-black uppercase text-xs tracking-widest px-6 py-4 rounded-2xl hover:opacity-90 transition-opacity disabled:opacity-40"
                    >
                        {loading ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
                        Enviar
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Agent;
