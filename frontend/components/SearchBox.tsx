"use client";

import { useState } from 'react';

interface SearchBoxProps {
    onSearch: (query: string) => void;
    isLoading: boolean;
}

export default function SearchBox({ onSearch, isLoading }: SearchBoxProps) {
    const [query, setQuery] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            onSearch(query);
        }
    };

    return (
        <div className="w-full max-w-3xl mx-auto mb-12 relative z-10">
            <form onSubmit={handleSubmit} className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-xl blur opacity-25 group-hover:opacity-60 transition duration-1000 group-hover:duration-200"></div>
                <div className="relative">
                    <input
                        type="text"
                        className="block w-full p-5 pl-6 text-lg text-white bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-xl shadow-2xl focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 focus:outline-none placeholder-slate-400 transition-all"
                        placeholder="Mevzuatta arama yapın (örn: Kredi risk limitleri nelerdir?)"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="absolute right-3 top-2.5 bottom-2.5 px-6 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-medium rounded-lg transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-cyan-500/25 flex items-center gap-2"
                    >
                        {isLoading ? (
                            <>
                                <div className="animate-spin h-5 w-5 border-2 border-white/30 border-b-white rounded-full"></div>
                                <span className="hidden sm:inline">Araştırılıyor...</span>
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                </svg>
                                <span className="hidden sm:inline">Ara</span>
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
}
