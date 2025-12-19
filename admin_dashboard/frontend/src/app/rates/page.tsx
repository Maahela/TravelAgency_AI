
"use client";

import React, { useEffect, useState } from 'react';
import { 
  Search, 
  Filter, 
  Download, 
  RefreshCcw,
  Calendar,
  ChevronRight,
  ChevronLeft,
  MoreVertical,
  Hotel
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getRates, updateRate } from '@/services/api';
import { Skeleton } from '@/components/ui/Skeleton';

interface Rate {
  id: string;
  hotel_name: string;
  room_type: string;
  rate_per_night: number;
  currency: string;
  meal_plan?: string;
  occupancy?: string;
  season_start_date: string;
  season_end_date: string;
  source?: string;
}

export default function RatesPage() {
  const [rates, setRates] = useState<Rate[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedRate, setSelectedRate] = useState<Rate | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const data = await getRates(search || undefined);
        setRates(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    const timer = setTimeout(() => fetchData(), 500);
    return () => clearTimeout(timer);
  }, [search]);

  return (
    <div className="space-y-8">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight mb-2">Hotel Rates</h2>
          <p className="text-muted-foreground text-sm">Centralized database of all extracted room rates</p>
        </div>
        <div className="flex gap-3">
          <button className="glass p-3 rounded-xl hover:bg-white/[0.05] transition-colors">
            <RefreshCcw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
          <button className="glass px-6 py-3 rounded-xl hover:bg-white/[0.05] transition-colors flex items-center gap-2 font-medium">
            <Download size={18} />
            Export CSV
          </button>
        </div>
      </header>

      <div className="flex gap-4">
        <div className="flex-1 relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-accent transition-colors" size={18} />
          <input 
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by hotel name..."
            className="w-full bg-card border border-card-border rounded-2xl pl-12 pr-6 py-4 focus:outline-none focus:border-accent/40 focus:ring-4 ring-accent/5 transition-all text-sm"
          />
        </div>
        <button className="glass px-6 py-4 rounded-2xl flex items-center gap-2 text-sm font-semibold">
          <Filter size={18} />
          Filters
        </button>
      </div>

      <div className="glass-card rounded-[2.5rem] overflow-hidden border border-white/[0.05]">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/[0.05] bg-white/[0.01]">
                <th className="px-8 py-5 text-xs font-bold uppercase tracking-wider text-muted-foreground">Hotel Property</th>
                <th className="px-8 py-5 text-xs font-bold uppercase tracking-wider text-muted-foreground">Room Details</th>
                <th className="px-8 py-5 text-xs font-bold uppercase tracking-wider text-muted-foreground">Seasonality</th>
                <th className="px-8 py-5 text-xs font-bold uppercase tracking-wider text-muted-foreground text-right">Rate</th>
                <th className="px-8 py-5 text-xs font-bold uppercase tracking-wider text-muted-foreground"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.03]">
              {loading ? (
                [1, 2, 3, 4, 5].map((i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-8 py-6">
                      <div className="flex items-center gap-4">
                        <Skeleton className="w-10 h-10 rounded-xl" />
                        <div className="space-y-2">
                          <Skeleton className="h-4 w-32" />
                          <Skeleton className="h-3 w-20" />
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-24" />
                        <div className="flex gap-2">
                           <Skeleton className="h-5 w-8 rounded" />
                           <Skeleton className="h-5 w-16 rounded" />
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <Skeleton className="h-4 w-32" />
                    </td>
                    <td className="px-8 py-6 text-right">
                       <Skeleton className="h-6 w-20 ml-auto" />
                       <Skeleton className="h-3 w-12 ml-auto mt-1" />
                    </td>
                    <td className="px-8 py-6 text-right">
                       <Skeleton className="h-8 w-8 rounded-lg ml-auto" />
                    </td>
                  </tr>
                ))
              ) : rates.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-8 py-20 text-center text-muted-foreground">
                    No rates found matching your search.
                  </td>
                </tr>
              ) : rates.map((rate, i) => (
                <motion.tr 
                  key={i} 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="hover:bg-white/[0.02] transition-colors group"
                >
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center text-accent">
                         <Hotel size={20} />
                      </div>
                      <div>
                        <p className="font-bold text-sm tracking-tight group-hover:text-accent transition-colors">
                          {rate.hotel_name}
                        </p>
                        <p className="text-[10px] text-muted-foreground uppercase font-semibold tracking-wider">
                          {rate.source || 'Airtable Sync'}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">{rate.room_type}</p>
                      <div className="flex gap-2">
                        <span className="text-[10px] bg-white/[0.05] px-2 py-0.5 rounded text-muted-foreground border border-white/[0.05]">
                          {rate.meal_plan || 'BB'}
                        </span>
                        {rate.occupancy && (
                          <span className="text-[10px] bg-accent-muted px-2 py-0.5 rounded text-accent font-bold">
                            {rate.occupancy}
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                       <Calendar size={14} className="text-accent/60" />
                       <span>{rate.season_start_date}</span>
                       <ChevronRight size={10} />
                       <span>{rate.season_end_date}</span>
                    </div>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <p className="text-base font-bold font-mono text-foreground">
                       {rate.currency} {rate.rate_per_night?.toLocaleString()}
                    </p>
                    <p className="text-[10px] text-emerald-500 font-bold">Net Rate</p>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <button 
                      onClick={() => {
                        setSelectedRate(rate);
                        setIsEditModalOpen(true);
                      }}
                      className="p-2 rounded-lg hover:bg-white/[0.05] text-accent transition-colors"
                    >
                      <MoreVertical size={16} />
                    </button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-8 py-5 border-t border-white/[0.05] flex justify-between items-center text-sm text-muted-foreground bg-white/[0.01]">
          <p>Showing <span className="text-foreground font-bold">{rates.length}</span> results</p>
          <div className="flex gap-2">
            <button className="p-2 rounded-xl glass hover:bg-white/[0.05] transition-colors disabled:opacity-30" disabled>
              <ChevronLeft size={18} />
            </button>
            <button className="p-2 rounded-xl glass hover:bg-white/[0.05] transition-colors">
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {isEditModalOpen && selectedRate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsEditModalOpen(false)}
            />
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 20 }}
              className="glass-card w-full max-w-lg p-8 rounded-[2.5rem] relative z-10 space-y-6"
            >
              <h3 className="text-2xl font-bold">Edit Rate Entry</h3>
              
              <form className="space-y-4" onSubmit={async (e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const data = {
                   hotel_name: formData.get('hotel_name'),
                   room_type: formData.get('room_type'),
                   price: formData.get('price'),
                   currency: formData.get('currency')
                };
                try {
                   await updateRate(selectedRate.id, data);
                   setIsEditModalOpen(false);
                   // Refresh
                   const updated = await getRates(search || undefined);
                   setRates(updated);
                } catch (err) {
                   console.error(err);
                   alert("Failed to update rate");
                }
              }}>
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold text-muted-foreground ml-2">Hotel Name</label>
                  <input name="hotel_name" defaultValue={selectedRate.hotel_name} className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-accent" />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold text-muted-foreground ml-2">Room Type</label>
                  <input name="room_type" defaultValue={selectedRate.room_type} className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-accent" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-[10px] uppercase font-bold text-muted-foreground ml-2">Price</label>
                    <input name="price" defaultValue={selectedRate.rate_per_night} className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-accent font-mono" />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] uppercase font-bold text-muted-foreground ml-2">Currency</label>
                    <input name="currency" defaultValue={selectedRate.currency} className="w-full bg-white/[0.04] border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-accent" />
                  </div>
                </div>
                
                <div className="flex gap-4 pt-4">
                  <button type="button" onClick={() => setIsEditModalOpen(false)} className="flex-1 px-6 py-3 rounded-xl glass hover:bg-white/10 transition-colors font-bold">
                    Cancel
                  </button>
                  <button type="submit" className="flex-1 px-6 py-3 rounded-xl bg-accent text-white shadow-lg hover:bg-accent/80 transition-colors font-bold">
                    Save Changes
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
