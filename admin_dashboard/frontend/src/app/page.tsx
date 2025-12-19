
"use client";

import React, { useEffect, useState } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Clock, 
  ArrowUpRight, 
  Package, 
  Activity,
  Calendar,
  Layers,
  Mail
} from 'lucide-react';
import { motion } from 'framer-motion';
import { getStats, getRates, getAnalytics } from '@/services/api';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const item = {
  hidden: { y: 20, opacity: 0 },
  show: { y: 0, opacity: 1 }
};

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [recentRates, setRecentRates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [s, r, a] = await Promise.all([getStats(), getRates(), getAnalytics()]);
        setStats(s);
        setRecentRates(r.slice(0, 5));
        setAnalytics(a);
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const statsCards = [
    { name: 'Total Rates', value: stats?.total_rates || '0', icon: BarChart3, color: 'text-blue-500' },
    { name: 'Price Items', value: stats?.total_price_items || '0', icon: Package, color: 'text-indigo-500' },
    { name: 'Processing Logs', value: stats?.total_logs || '0', icon: Activity, color: 'text-emerald-500' },
    { name: 'Live Hotels', value: '24', icon: Layers, color: 'text-violet-500' },
  ];

  return (
    <div className="space-y-12">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-4xl font-bold tracking-tight mb-2">Command Center</h2>
          <p className="text-muted-foreground">Overview of your hotel intelligence network</p>
        </div>
        <div className="flex gap-4">
          <div className="glass px-4 py-2 rounded-xl flex items-center gap-2 text-sm font-medium">
            <Calendar size={16} className="text-accent" />
            <span>Dec 19, 2025</span>
          </div>
        </div>
      </header>

      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {statsCards.map((card) => (
          <motion.div 
            key={card.name} 
            variants={item}
            className="glass-card p-6 rounded-3xl group hover:border-accent/40 transition-colors"
          >
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 rounded-2xl bg-white/[0.03] ${card.color}`}>
                <card.icon size={24} />
              </div>
              <div className="p-1 px-2 rounded-lg bg-emerald-500/10 text-emerald-500 text-[10px] font-bold flex items-center gap-1">
                <TrendingUp size={10} />
                +12%
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground font-medium mb-1">{card.name}</p>
              <h3 className="text-3xl font-bold font-mono">
                {loading ? '...' : card.value}
              </h3>
            </div>
          </motion.div>
        ))}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        <div className="lg:col-span-2 space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Clock size={20} className="text-accent" />
              Recent Extractions
            </h3>
            <button className="text-xs font-semibold text-accent flex items-center gap-1 hover:underline">
              View All <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="glass-card rounded-3xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-card-border bg-white/[0.01]">
                    <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Hotel</th>
                    <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Room Type</th>
                    <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Price</th>
                    <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-card-border">
                  {loading ? (
                    [1,2,3].map(i => (
                      <tr key={i} className="animate-pulse">
                        <td colSpan={4} className="px-6 py-4 h-16 bg-white/[0.02]" />
                      </tr>
                    ))
                  ) : recentRates.map((rate, i) => (
                    <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="px-6 py-4">
                        <p className="font-semibold text-sm group-hover:text-accent transition-colors">{rate.hotel_name}</p>
                        <p className="text-[10px] text-muted-foreground">{rate.source || 'Email Extraction'}</p>
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">{rate.room_type}</td>
                      <td className="px-6 py-4 font-mono text-sm font-bold">
                        {rate.currency} {rate.rate_per_night?.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold">Verified</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <h3 className="text-xl font-bold flex items-center gap-2">
            <TrendingUp size={20} className="text-accent" />
            Extraction Performance
          </h3>
          <div className="glass-card p-6 rounded-3xl space-y-6">
             <div className="flex justify-between items-end h-32 gap-2">
                {analytics ? Object.entries(analytics.processing_stats).map(([label, count]: [string, any]) => {
                   const max = Math.max(...Object.values(analytics.processing_stats) as number[]);
                   const height = (count / max) * 100;
                   return (
                      <div key={label} className="flex-1 flex flex-col items-center gap-2 h-full justify-end group">
                         <div className="text-[10px] font-bold text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">{count}</div>
                         <motion.div 
                            initial={{ height: 0 }}
                            animate={{ height: `${height}%` }}
                            className={`w-full rounded-t-lg shadow-lg transition-colors
                               ${label === 'success' ? 'bg-emerald-500/40 hover:bg-emerald-500/60' : 'bg-red-500/40 hover:bg-red-500/60'}`}
                         />
                         <div className="text-[9px] font-bold uppercase tracking-tighter truncate w-full text-center">{label}</div>
                      </div>
                   )
                }) : (
                   <div className="w-full flex items-center justify-center text-muted-foreground text-xs italic">Loading trends...</div>
                )}
             </div>
             <div className="pt-4 border-t border-card-border flex justify-between items-center text-[11px]">
                <span className="text-muted-foreground">Total Processed</span>
                <span className="font-bold">{analytics?.total_processed || 0}</span>
             </div>
          </div>

          <h3 className="text-xl font-bold flex items-center gap-2">
            <Clock size={20} className="text-accent" />
            Live Feed
          </h3>
          <div className="space-y-4">
             {recentRates.slice(0, 3).map((rate, i) => (
                <div key={i} className="glass-card p-4 rounded-2xl flex gap-4 items-start relative overflow-hidden group">
                   <div className="absolute top-0 left-0 w-1 h-full bg-accent opacity-30" />
                   <div className="w-10 h-10 rounded-xl bg-white/[0.03] flex-shrink-0 flex items-center justify-center text-muted-foreground">
                      <Mail size={18} />
                   </div>
                   <div className="space-y-1">
                      <p className="text-sm font-semibold truncate">Rate extracted</p>
                      <p className="text-[10px] text-muted-foreground">{rate.hotel_name} • Just now</p>
                      <p className="text-[11px] text-muted-foreground line-clamp-2">Successfully parsed {rate.room_type} at {rate.currency} {rate.rate_per_night}.</p>
                   </div>
                </div>
             ))}
          </div>
        </div>
      </div>
    </div>
  );
}
