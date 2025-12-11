"use client";

import ReactMarkdown from 'react-markdown';

interface Source {
    source: string;
    page: string | number;
    type?: string;
    [key: string]: any;
}

interface ResultListProps {
    answer: string;
    sources: Source[];
}

export default function ResultList({ answer, sources }: ResultListProps) {
    return (
        <div className="w-full max-w-4xl mx-auto space-y-8 animate-fade-in-up">
            {/* Answer Card */}
            <div className="bg-slate-900/60 backdrop-blur-md border border-slate-700/50 rounded-2xl p-8 shadow-2xl relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-cyan-500 to-teal-500"></div>

                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-lg border border-cyan-500/20">
                        <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                        Müfettiş Analizi
                    </h2>
                </div>

                <div className="prose prose-invert prose-lg max-w-none prose-a:text-cyan-400 hover:prose-a:text-cyan-300 prose-headings:text-slate-200 prose-strong:text-white">
                    <ReactMarkdown>{answer}</ReactMarkdown>
                </div>
            </div>

            {/* Sources Grid */}
            {sources.length > 0 && (
                <div className="mt-8">
                    <h3 className="text-lg font-medium text-slate-400 mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                        </svg>
                        Referans Kaynaklar
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {sources.map((src, idx) => (
                            <div
                                key={idx}
                                className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-4 hover:bg-slate-800/60 hover:border-cyan-500/30 transition-all duration-300 cursor-pointer group"
                            >
                                <div className="flex items-start justify-between">
                                    <span className="inline-flex items-center justify-center w-6 h-6 text-xs font-bold text-slate-900 bg-cyan-500/80 rounded-full group-hover:bg-cyan-400 transition-colors">
                                        {idx + 1}
                                    </span>
                                    <span className="text-xs text-slate-500 font-mono border border-slate-700 rounded px-1.5 py-0.5">
                                        {src.type || 'text'}
                                    </span>
                                </div>
                                <div className="mt-3">
                                    <a
                                        href={`http://localhost:8000/pdfs/${src.source}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-sm font-medium text-slate-200 line-clamp-2 hover:text-cyan-400 hover:underline transition-colors block"
                                        title={`${src.source} (PDF)`}
                                    >
                                        {src.source}
                                        <span className="inline-block ml-1 text-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity">↗</span>
                                    </a>
                                    <p className="text-xs text-slate-400 mt-1">
                                        Sayfa: {src.page}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
