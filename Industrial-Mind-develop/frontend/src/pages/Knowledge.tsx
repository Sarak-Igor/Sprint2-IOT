import React, { useState } from 'react';
import { Search, BookOpen, FileText, Download, ExternalLink, Info, Book } from 'lucide-react';

const Knowledge = () => {
    const [search, setSearch] = useState('');

    const manuals = [
        { 
            title: 'Manual Geral de Motores BT', 
            category: 'Técnico', 
            file: 'WEG-w22-motor-eletrico-trifasico-brochure.pdf',
            size: '24.1 MB',
            tags: ['W22', 'Instalação', 'Manutenção']
        },
        { 
            title: 'Requisitos do Sistema Forzy', 
            category: 'Especificação', 
            file: 'forzy-requisitos.pdf',
            size: '1.7 MB',
            tags: ['Projeto', 'Scope', 'Requisitos']
        },
        { 
            title: 'Mapa Mental de Arquitetura', 
            category: 'Arquitetura', 
            file: 'forzy-mapa-mental.pdf',
            size: '0.1 MB',
            tags: ['Estrutura', 'Fluxo', 'Design']
        }
    ];

    const glossary = [
        { term: 'Carcaca', definition: 'Estrutura externa do motor que suporta o estator e protege os componentes internos.' },
        { term: 'IP55', definition: 'Grau de proteção contra entrada de poeira e jatos de água de qualquer direção.' },
        { term: 'Classe F', definition: 'Limite de temperatura de isolamento de 155°C, garantindo durabilidade térmica.' },
        { term: 'Fator de Serviço (FS)', definition: 'Multiplicador que indica a sobrecarga permissível que o motor pode suportar continuamente.' },
        { term: 'Escorregamento', definition: 'Diferença entre a velocidade síncrona e a velocidade real de rotação do motor.' }
    ];


    const handleDownload = (fileName: string, e?: React.MouseEvent) => {
        if (e) e.stopPropagation();
        
        const link = document.createElement('a');
        link.href = `/${fileName}`;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleOpen = (fileName: string) => {
        window.open(`/${fileName}`, '_blank');
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

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                {/* Coluna de Manuais */}
                <div className="lg:col-span-2 flex flex-col gap-6">
                    <div className="flex items-center gap-3">
                        <FileText size={20} className="text-[var(--theme-primary)]" />
                        <h2 className="text-sm font-black text-white uppercase tracking-widest">Documentação Técnica</h2>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {manuals.filter(m => m.title.toLowerCase().includes(search.toLowerCase()) || m.tags.some(t => t.toLowerCase().includes(search.toLowerCase()))).map((doc, i) => (
                            <div 
                                key={i} 
                                onClick={() => handleOpen(doc.file)}
                                className="bg-theme-card border-theme p-6 rounded-theme hover:bg-white/[0.04] transition-all group cursor-pointer border-l-2 border-l-transparent hover:border-l-[var(--theme-primary)]"
                            >
                                <div className="flex justify-between items-start mb-6">
                                    <div className="p-3 bg-white/5 rounded-xl text-white/40 group-hover:text-[var(--theme-primary)] transition-colors">
                                        <BookOpen size={24} />
                                    </div>
                                    <button 
                                        onClick={(e) => handleDownload(doc.file, e)}
                                        className="p-2 bg-white/5 rounded-lg text-white/20 hover:text-white transition-colors"
                                    >
                                        <Download size={16} />
                                    </button>
                                </div>
                                <h4 className="text-base font-black text-white uppercase tracking-tight mb-2 leading-tight">{doc.title}</h4>
                                <div className="flex flex-wrap gap-2 mb-4">
                                    {doc.tags.map(tag => (
                                        <span key={tag} className="text-[8px] font-black text-white/20 bg-white/5 px-2 py-0.5 rounded uppercase tracking-widest">{tag}</span>
                                    ))}
                                </div>
                                <div className="flex items-center justify-between mt-auto pt-4 border-t border-white/5">
                                    <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">{doc.size}</span>
                                    <span className="text-[10px] font-black text-[var(--theme-primary)] uppercase tracking-widest flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        Abrir <ExternalLink size={10} />
                                    </span>
                                </div>
                            </div>
                        ))}
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

