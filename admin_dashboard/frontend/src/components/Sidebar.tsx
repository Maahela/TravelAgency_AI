
"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  BarChart3, 
  MessageSquare, 
  Table, 
  Settings, 
  Users, 
  ShieldCheck,
  Package
} from 'lucide-react';
import { motion } from 'framer-motion';

const navigation = [
  { name: 'Dashboard', href: '/', icon: BarChart3 },
  { name: 'Hotel Rates', href: '/rates', icon: Table },
  { name: 'Price Items', href: '/price-items', icon: Package },
  { name: 'Chat Bot', href: '/chat', icon: MessageSquare },
  { name: 'Contacts', href: '/contacts', icon: Users },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-72 h-screen flex flex-col border-r border-card-border bg-card/40 backdrop-blur-xl sticky top-0">
      <div className="p-8 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center text-white shadow-[0_0_20px_rgba(99,102,241,0.4)]">
          <ShieldCheck size={24} />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-tight">JAKEmail</h1>
          <p className="text-[10px] text-muted-foreground uppercase tracking-widest font-semibold font-mono">Admin Console</p>
        </div>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 
                ${isActive 
                  ? 'text-accent bg-accent/10 font-medium' 
                  : 'text-neutral-500 hover:text-white hover:bg-white/[0.03]'}`}
            >
              <item.icon size={20} strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-sm">{item.name}</span>
              {isActive && (
                <motion.div
                  layoutId="active-pill"
                  className="ml-auto w-1.5 h-1.5 rounded-full bg-accent"
                />
              )}
            </Link>
          );
        })}
      </nav>


    </div>
  );
}
