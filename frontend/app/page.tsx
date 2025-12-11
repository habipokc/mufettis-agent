"use client";

import { useState } from 'react';
import SearchBox from '@/components/SearchBox';
import ResultList from '@/components/ResultList';

export default function Home() {
  const [answer, setAnswer] = useState<string>('');
  const [sources, setSources] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setHasSearched(true);
    setAnswer('');

    try {
      const res = await fetch('http://localhost:8000/api/v1/search/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 5 }),
      });

      if (!res.ok) {
        if (res.status === 429) {
          throw new Error("⚠️ Google Gemini API kotası doldu. (Free Tier limitine takıldınız). Lütfen 1-2 dakika bekleyip tekrar deneyin.");
        }
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Arama işlemi başarısız oldu.');
      }

      const data = await res.json();
      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (error: any) {
      console.error(error);
      setAnswer(`⚠️ **Hata:** ${error.message}\n\nGoogle Gemini API kotası dolmuş olabilir. Lütfen bir süre sonra tekrar deneyin.`);
      setSources([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-white selection:bg-cyan-500/30">
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-900/20 rounded-full blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-[20%] right-[-10%] w-[30%] h-[30%] bg-cyan-900/20 rounded-full blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-[-10%] left-[20%] w-[35%] h-[35%] bg-indigo-900/20 rounded-full blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 max-w-6xl mx-auto px-4 py-12 md:py-20 flex flex-col items-center min-h-screen">

        {/* Hero Section */}
        <div className={`transition-all duration-700 ease-in-out flex flex-col items-center ${hasSearched ? 'mb-8' : 'mb-16 mt-20'}`}>
          <div className="mb-6 relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full blur opacity-30"></div>
            <div className="relative px-4 py-1 bg-slate-900 rounded-full border border-slate-700/50 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="text-xs font-medium text-cyan-400 tracking-wider uppercase">Beta v0.1</span>
            </div>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-center tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400">
            Müfettiş<span className="text-cyan-500">.ai</span>
          </h1>

          <p className={`text-lg md:text-xl text-slate-400 text-center max-w-2xl transition-all duration-500 ${hasSearched ? 'opacity-0 h-0 overflow-hidden' : 'opacity-100'}`}>
            Banka mevzuatı, kanunlar ve yönetmeliklerde yapay zeka destekli anlık arama.
            Karmaşık maddeleri saniyeler içinde analiz edin.
          </p>
        </div>

        {/* Search Interface */}
        <SearchBox onSearch={handleSearch} isLoading={isLoading} />

        {/* Results Area */}
        {hasSearched && (
          <div className="w-full transition-all duration-500 animate-fade-in">
            <ResultList answer={answer} sources={sources} />
          </div>
        )}

        {/* Footer info (only visible initially) */}
        {!hasSearched && (
          <div className="mt-auto pt-20 text-center text-slate-600 text-sm">
            <p>Powered by Google Gemini 2.5 Flash & ChromaDB</p>
          </div>
        )}

      </div>
    </main>
  );
}
