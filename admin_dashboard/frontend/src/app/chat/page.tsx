
"use client";

import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  RotateCcw, 
  Trash2,
  Copy,
  Check
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { sendMessage } from '@/services/api';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  role: 'bot' | 'user';
  text: string;
  timestamp: Date;
}

const SUGGESTED_PROMPTS = [
  "Show me rates for Galle Face Hotel",
  "Find rooms for 2 people under $200",
  "Calculate budget for 3 nights at Galle Face Hotel",
  "Find email for Hilton Colombo",
  "What's the HB rate at Galle Face?",
  "help"
];

export default function ChatPage() {
const SESSION_KEY = 'jakemail_chat_history_v1';

  const [messages, setMessages] = useState<Message[]>([]);
  const [mounted, setMounted] = useState(false);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initial load
  useEffect(() => {
    setMounted(true);
    try {
      const savedSession = localStorage.getItem(SESSION_KEY);
      if (savedSession) {
        const parsed = JSON.parse(savedSession);
        const hydratedMessages = parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(hydratedMessages);
      } else {
        // Only set default greeting if no history exists
        setMessages([{
          id: '1',
          role: 'bot',
          text: 'Hello! I am your JAKEmail Assistant. How can I help you with your hotel intelligence today?',
          timestamp: new Date()
        }]);
      }
    } catch (err) {
      console.error('Failed to load chat session:', err);
      // Fallback
      setMessages([{
        id: '1',
        role: 'bot',
        text: 'Hello! I am your JAKEmail Assistant. How can I help you with your hotel intelligence today?',
        timestamp: new Date()
      }]);
    }
  }, []);

  // Save changes ONLY after mounted and we have valid state
  useEffect(() => {
    if (mounted && messages.length > 0) {
      localStorage.setItem(SESSION_KEY, JSON.stringify(messages));
    }
  }, [messages, mounted]);

  // Save session to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem(SESSION_KEY, JSON.stringify(messages));
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleNewSession = () => {
    const defaultMsg: Message = {
      id: Date.now().toString(),
      role: 'bot',
      text: 'Started a new session! How can I help you now?',
      timestamp: new Date()
    };
    setMessages([defaultMsg]);
    localStorage.setItem(SESSION_KEY, JSON.stringify([defaultMsg]));
  };

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear your entire chat history?')) {
      const defaultMsg: Message = {
        id: Date.now().toString(),
        role: 'bot',
        text: 'History cleared. Ready for a fresh start!',
        timestamp: new Date()
      };
      setMessages([defaultMsg]);
      localStorage.removeItem(SESSION_KEY);
    }
  };

  const handleSend = async (e?: React.FormEvent, promptText?: string) => {
    e?.preventDefault();
    const messageText = promptText || input;
    if (!messageText.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: messageText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const data = await sendMessage(messageText);
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
            onClick={handleNewSession}
            className="p-3 rounded-xl glass hover:bg-white/[0.05] text-muted-foreground transition-colors flex items-center gap-2"
            title="Start New Session"
          >
            <RotateCcw size={18} />
            <span className="text-xs font-semibold hidden sm:inline">New Session</span>
          </button>
          <button 
            onClick={handleClearHistory}
            className="p-3 rounded-xl glass hover:bg-white/[0.05] text-red-400/80 hover:text-red-400 transition-colors flex items-center gap-2"
            title="Clear History"
          >
            <Trash2 size={18} />
            <span className="text-xs font-semibold hidden sm:inline">Clear</span>
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
                  <div className={`group/message relative px-6 py-4 rounded-3xl text-[15px] leading-relaxed
                    ${msg.role === 'user' 
                      ? 'bg-accent text-white rounded-tr-none' 
                      : 'bg-white/[0.03] border border-card-border rounded-tl-none'}`}
                  >
                    {msg.role === 'bot' ? (
                      <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="whitespace-pre-wrap">{msg.text}</p>
                    )}
                    {msg.role === 'bot' && (
                      <button
                        onClick={() => copyToClipboard(msg.text, msg.id)}
                        className="absolute top-2 right-2 p-2 rounded-lg bg-white/5 hover:bg-white/10 opacity-0 group-hover/message:opacity-100 transition-opacity"
                        title="Copy message"
                      >
                        {copiedId === msg.id ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                      </button>
                    )}
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

        {messages.length === 1 && (
          <div className="px-6 pb-4 border-b border-card-border">
            <p className="text-xs text-muted-foreground mb-3 font-semibold">Quick Start:</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_PROMPTS.map((prompt, idx) => (
                <motion.button
                  key={idx}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  onClick={() => handleSend(undefined, prompt)}
                  className="px-3 py-1.5 text-xs rounded-full bg-white/5 border border-card-border hover:border-accent/50 hover:bg-white/10 transition-all"
                >
                  {prompt}
                </motion.button>
              ))}
            </div>
          </div>
        )}

        <div className="p-6 bg-white/[0.02] border-t border-card-border">
          <form onSubmit={handleSend} className="relative flex items-center gap-4">
             <div className="flex-1 relative group">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about hotel rates, supplements or budgets... (type 'help' for examples)"
                  className="w-full bg-white/[0.04] border border-card-border rounded-2xl px-6 py-4 focus:outline-none focus:border-accent/50 focus:bg-white/[0.06] transition-all"
                />
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
