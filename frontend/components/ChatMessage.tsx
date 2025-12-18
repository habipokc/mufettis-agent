import React from 'react';
import ReactMarkdown from 'react-markdown';
// import { ResultListProps } from './ResultList'; // Removed unused import

// Define types locally if needed to avoid circular deps, or import from a shared types file
interface Source {
    source: string;
    page: any;
    type?: string;
    text?: string;
}

interface ChatMessageProps {
    role: 'user' | 'assistant';
    content: string;
    sources?: Source[];
}

export default function ChatMessage({ role, content, sources }: ChatMessageProps) {
    const isUser = role === 'user';

    return (
        <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6 group animate-fade-in`}>

            {/* Avatar for Assistant */}
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-xs font-bold text-white shadow-lg mr-3 mt-1 flex-shrink-0">
                    T
                </div>
            )}

            <div className={`relative max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-4 shadow-xl ${isUser
                ? 'bg-gradient-to-br from-blue-600 to-cyan-600 text-white rounded-br-none'
                : 'bg-white border border-slate-200 text-slate-800 dark:bg-slate-800/80 dark:border-slate-700/50 dark:text-slate-200 rounded-bl-none backdrop-blur-sm'
                }`}>
                {/* Message Content */}
                <div className={`prose prose-invert max-w-none text-sm md:text-base leading-relaxed break-words ${isUser ? 'prose-p:text-white' : ''}`}>
                    {isUser ? (
                        <p className="whitespace-pre-wrap">{content}</p>
                    ) : (
                        <ReactMarkdown>{content}</ReactMarkdown>
                    )}
                </div>

                {/* Sources Section (Only for Assistant if sources exist) */}
                {!isUser && sources && sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-slate-700/50">
                        <p className="text-xs font-semibold text-cyan-400 mb-2 flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
                            </svg>
                            REFERANSLAR
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {sources.map((src, idx) => {
                                // Extract filename for display
                                const fileName = src.source.split('\\').pop()?.split('/').pop() || src.source;
                                // Use Next.js API proxy route for PDFs (avoids Mixed Content and Docker DNS issues)
                                const pdfUrl = `/api/pdfs/${encodeURIComponent(fileName)}`;

                                return (
                                    <a
                                        key={idx}
                                        href={pdfUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 hover:border-cyan-500/50 rounded-lg text-xs text-slate-700 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyan-300 transition-all duration-200 group/source"
                                    >
                                        <span className="truncate max-w-[150px] font-medium">{fileName}</span>
                                        {src.page && (
                                            <span className="px-1.5 py-0.5 bg-slate-800 rounded-md text-[10px] text-slate-400 group-hover/source:text-cyan-400 transition-colors">
                                                S.{src.page}
                                            </span>
                                        )}
                                    </a>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            {/* Avatar for User */}
            {isUser && (
                <div className="w-8 h-8 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center text-xs font-bold text-slate-300 shadow-lg ml-3 mt-1 flex-shrink-0">
                    S
                </div>
            )}
        </div>
    );
}
