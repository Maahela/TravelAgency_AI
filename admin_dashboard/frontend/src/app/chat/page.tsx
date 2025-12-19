
"use client";

import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  RotateCcw, 
  Trash2,
  Paperclip,
  Maximize2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { sendMessage } from '@/services/api';

interface Message {
  id: string;
  role: 'bot' | 'user';
  text: string;
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'bot',
      text: 'Hello! I am your JAKEmail Assistant. How can I help you with your hotel intelligence today?',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const data = await sendMessage(input);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        text: data.response,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'bot',
        text: 'Sorry, I encountered an error. Please try again later.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col space-y-6">
      <header className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight mb-1 flex items-center gap-3">
            <Sparkles className="text-accent" />
            JAKEmail Assistant
          </h2>
          <p className="text-muted-foreground text-sm">Interactive hotel intelligence & budget calculation</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => setMessages([messages[0]])}
            className="p-3 rounded-xl glass hover:bg-white/[0.05] text-muted-foreground transition-colors"
            title="Reset Conversation"
          >
            <RotateCcw size={18} />
          </button>
          <button 
            className="p-3 rounded-xl glass hover:bg-white/[0.05] text-muted-foreground transition-colors"
            title="Clear All"
          >
            <Trash2 size={18} />
          </button>
        </div>
      </header>

      <div className="flex-1 glass-card rounded-[2rem] flex flex-col overflow-hidden relative">
        <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
          <AnimatePresence mode="popLayout">
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`w-10 h-10 rounded-2xl flex-shrink-0 flex items-center justify-center shadow-lg
                  ${msg.role === 'user' 
                    ? 'bg-accent text-white' 
                    : 'bg-white/[0.05] text-accent border border-card-border'}`}
                >
                  {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                </div>
                <div className={`max-w-[70%] space-y-2 ${msg.role === 'user' ? 'items-end' : ''}`}>
                  <div className={`px-6 py-4 rounded-3xl text-[15px] leading-relaxed
                    ${msg.role === 'user' 
                      ? 'bg-accent text-white rounded-tr-none' 
                      : 'bg-white/[0.03] border border-card-border rounded-tl-none'}`}
                  >
                    <p className="whitespace-pre-wrap">{msg.text}</p>
                  </div>
                  <p className="text-[10px] text-muted-foreground px-2">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {isTyping && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex gap-4"
            >
              <div className="w-10 h-10 rounded-2xl bg-white/[0.05] flex items-center justify-center text-accent">
                <Bot size={20} />
              </div>
              <div className="px-6 py-4 rounded-3xl bg-white/[0.03] border border-card-border rounded-tl-none flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-6 bg-white/[0.02] border-t border-card-border">
          <form onSubmit={handleSend} className="relative flex items-center gap-4">
             <div className="flex-1 relative group">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about hotel rates, supplements or budgets..."
                  className="w-full bg-white/[0.04] border border-card-border rounded-2xl px-6 py-4 pr-32 focus:outline-none focus:border-accent/50 focus:bg-white/[0.06] transition-all"
                />
                <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
                   <button type="button" className="p-2 text-muted-foreground hover:text-foreground transition-colors">
                      <Paperclip size={18} />
                   </button>
                   <button type="button" className="p-2 text-muted-foreground hover:text-foreground transition-colors">
                      <Maximize2 size={18} />
                   </button>
                </div>
             </div>
             <button
               type="submit"
               disabled={!input.trim() || isTyping}
               className="p-4 rounded-2xl bg-accent text-white shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:scale-105 active:scale-95 disabled:opacity-50 disabled:scale-100 transition-all font-bold"
             >
               <Send size={20} />
             </button>
          </form>
          <p className="text-center text-[10px] text-muted-foreground mt-4">
            AI can make mistakes. Verify important financial data.
          </p>
        </div>
      </div>
    </div>
  );
}
