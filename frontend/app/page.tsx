"use client";

import { useState, useRef, useEffect } from 'react';
import SearchBox from '@/components/SearchBox';
import ChatMessage from '@/components/ChatMessage';
import ThemeToggle from '@/components/ThemeToggle';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSearch = async (query: string) => {
    // 1. Add User Message immediately
    const userMsg: Message = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // 2. Call API
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/v1/search/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 5 }),
      });

      if (!res.ok) {
        if (res.status === 429) {
          throw new Error("⚠️ Google Gemini API kotası doldu. Lütfen 1-2 dakika bekleyip tekrar deneyin.");
        }
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'İstek başarısız oldu.');
      }

      const data = await res.json();

      // 3. Add Assistant Message
      const botMsg: Message = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources
      };
      setMessages(prev => [...prev, botMsg]);

    } catch (error: any) {
      console.error(error);

      let displayMsg = error.message;
      if (typeof error.message === 'string' && error.message.includes('503')) {
        displayMsg = "Servis şuan yoğun kullanıma yanıt veremiyor. Lütfen 1-2 dakika bekleyin veya planınızı yükseltin.";
      }

      const errorMsg: Message = {
        role: 'assistant',
        content: `⚠️ **Hata:** ${displayMsg}`
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <main className="flex flex-col h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white selection:bg-cyan-500/30 overflow-hidden transition-colors duration-300">

      {/* Theme Toggle - Fixed Position */}
      <div className="fixed top-6 right-6 z-[100]">
        <ThemeToggle />
      </div>

      {/* Background Ambience */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-900/20 rounded-full blur-3xl opacity-30 animate-blob"></div>
        <div className="absolute top-[20%] right-[-10%] w-[30%] h-[30%] bg-cyan-900/20 rounded-full blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-[-10%] left-[20%] w-[35%] h-[35%] bg-indigo-900/20 rounded-full blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      {/* Main Content Area (Scrollable) */}
      <div className="flex-1 overflow-y-auto z-10 w-full scroll-smooth">
        <div className="max-w-4xl mx-auto px-4 py-8 min-h-full flex flex-col justify-center">

          {/* Hero Section (Hidden when chatting starts) */}
          {!hasMessages && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] transition-all duration-700">
              <div className="mb-6 relative animate-fade-in-up">
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full blur opacity-30"></div>
                <div className="relative px-4 py-1 bg-white dark:bg-slate-900 rounded-full border border-slate-200 dark:border-slate-700/50 flex items-center gap-2 shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-cyan-500 dark:bg-cyan-400 animate-pulse"></span>
                  <span className="text-xs font-medium text-cyan-600 dark:text-cyan-400 tracking-wider uppercase">Teftiş Agent v1.0</span>
                </div>
              </div>

              <h1 className="text-5xl md:text-7xl font-bold text-center tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-b from-slate-900 to-slate-500 dark:from-white dark:to-slate-400 animate-fade-in-up delay-100">
                Teftiş <span className="text-cyan-600 dark:text-cyan-500">Agent</span>
              </h1>

              <p className="text-lg md:text-xl text-slate-600 dark:text-slate-400 text-center max-w-2xl animate-fade-in-up delay-200">
                Bankacılık mevzuatı, kanunlar ve yönetmeliklerde yapay zeka destekli anlık uzman desteği.
              </p>
            </div>
          )}

          {/* Chat History */}
          {hasMessages && (
            <div className="flex flex-col gap-4 pb-32 pt-10">
              {messages.map((msg, idx) => (
                <ChatMessage
                  key={idx}
                  role={msg.role}
                  content={msg.content}
                  sources={msg.sources}
                />
              ))}

              {/* Loading Indicator (Tiny bubble) */}
              {isLoading && (
                <div className="flex justify-start mb-6 animate-pulse">
                  <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center mr-3">...</div>
                  <div className="bg-slate-800/50 rounded-2xl px-4 py-3 text-slate-400 text-sm">
                    Yazıyor...
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Input Area (Fixed Bottom) */}
      <div className="z-20 p-4 bg-gradient-to-t from-slate-50 via-slate-50/90 to-transparent dark:from-slate-950 dark:via-slate-950/90">
        <div className="max-w-3xl mx-auto">
          <SearchBox onSearch={handleSearch} isLoading={isLoading} />

          <div className="text-center text-slate-600 text-xs mt-4 opacity-70">
            Teftiş Agent hata yapabilir. Lütfen mevzuatı asıl kaynaklardan da kontrol edin.
          </div>
        </div>
      </div>

    </main>
  );
}
