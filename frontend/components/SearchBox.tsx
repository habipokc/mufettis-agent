"use client";

import { useState, useRef, useEffect } from 'react';

interface SearchBoxProps {
    onSearch: (query: string) => void;
    isLoading: boolean;
}

export default function SearchBox({ onSearch, isLoading }: SearchBoxProps) {
    const [query, setQuery] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-focus textarea when component mounts and after loading completes
    useEffect(() => {
        if (!isLoading && textareaRef.current) {
            textareaRef.current.focus();
        }
    }, [isLoading]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query);
            setQuery(''); // Clear input after search
        }
    };

    return (
        <div className="w-full max-w-3xl mx-auto relative z-10">
            <form onSubmit={handleSubmit} className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-xl blur opacity-25 group-hover:opacity-60 transition duration-1000 group-hover:duration-200"></div>
                <div className="relative bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border border-slate-200 dark:border-slate-700/50 rounded-xl shadow-2xl overflow-hidden p-2">
                    <textarea
                        ref={textareaRef}
                        className="block w-full p-4 text-lg text-slate-900 dark:text-white bg-transparent border-none focus:ring-0 focus:outline-none placeholder-slate-500 dark:placeholder-slate-400 resize-none min-h-[80px]"
                        placeholder="Mevzuatta arama yapın veya sohbet edin (örn: Kredi risk limitleri nelerdir?)"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSubmit(e);
                            }
                        }}
                        disabled={isLoading}
                        rows={3}
                    />
                    <div className="flex justify-end px-2 pb-2">
                        <button
                            type="submit"
                            disabled={isLoading || !query.trim()}
                            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-medium rounded-lg transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-cyan-500/25 flex items-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <div className="animate-spin h-5 w-5 border-2 border-white/30 border-b-white rounded-full"></div>
                                    <span className="hidden sm:inline">Düşünüyor...</span>
                                </>
                            ) : (
                                <>
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                    <span className="">Gönder</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
}
