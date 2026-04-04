"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Terminal, Database, Sparkles } from 'lucide-react';

export default function AxonChat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Axon Core Online. Ready for RAG or System Tool execution.", route: 'system' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat/orchestrator', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input }),
      });

      const data = await response.json();
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: data.response,
        route: data.route_taken 
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: "Error: Could not connect to Axon Backend. Ensure Docker is running.",
        route: 'error' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex flex-col h-screen bg-slate-950 text-slate-100 font-sans">
      <header className="p-4 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Bot size={20} className="text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight">AXON <span className="text-blue-500">CORE</span></h1>
        </div>
        <div className="flex gap-4 text-xs font-mono text-slate-400">
          <span className="flex items-center gap-1"><div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"/> API: 8000</span>
          <span className="flex items-center gap-1"><div className="w-2 h-2 bg-blue-500 rounded-full"/> QDRANT: 6333</span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded flex items-center justify-center shrink-0 ${
                msg.role === 'user' ? 'bg-slate-700' : 'bg-blue-900/30 text-blue-400 border border-blue-800/50'
              }`}>
                {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
              </div>
              
              <div className={`p-4 rounded-2xl ${
                msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-slate-900 border border-slate-800 rounded-tl-none'
              }`}>
                {msg.route && msg.role === 'assistant' && (
                  <div className="flex items-center gap-1.5 mb-2 text-[10px] uppercase tracking-widest font-bold opacity-50">
                    {msg.route === 'rag' && <><Database size={10} /> Knowledge Base</>}
                    {msg.route === 'tools' && <><Terminal size={10} /> System Tool</>}
                    {msg.route === 'general' && <><Sparkles size={10} /> General AI</>}
                  </div>
                )}
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-slate-900 p-4 rounded-2xl rounded-tl-none border border-slate-800 text-slate-500 text-xs italic">
              Axon is processing...
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      <div className="p-6 bg-slate-950 border-t border-slate-900">
        <div className="max-w-4xl mx-auto relative">
          <input
            className="w-full bg-slate-900 border border-slate-800 rounded-xl py-4 pl-4 pr-14 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all placeholder:text-slate-600 text-sm"
            placeholder="Ask Kunal's AI anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button 
            onClick={handleSend}
            className="absolute right-2 top-2 bottom-2 px-4 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors flex items-center justify-center"
          >
            <Send size={18} />
          </button>
        </div>
        <p className="text-[10px] text-center mt-4 text-slate-600 uppercase tracking-widest">
          Hybrid RAG + System Automation Engine
        </p>
      </div>
    </main>
  );
}