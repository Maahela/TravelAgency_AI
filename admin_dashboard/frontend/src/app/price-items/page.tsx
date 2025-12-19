
"use client";

import React, { useEffect, useState } from 'react';
import { 
  Package, 
  Search, 
  Tag, 
  Info,
  Calendar,
  Layers,
  ArrowUpRight,
  TrendingUp,
  CreditCard
} from 'lucide-react';
import { motion } from 'framer-motion';
import { getPriceItems } from '@/services/api';

const categoryColors: Record<string, string> = {
  meal_rate: 'bg-orange-500/10 text-orange-500',
  meal_plan_supplement: 'bg-blue-500/10 text-blue-500',
  extra_person_charge: 'bg-emerald-500/10 text-emerald-500',
  extra_bed_charge: 'bg-violet-500/10 text-violet-500',
  child_rate: 'bg-pink-500/10 text-pink-500',
  other_charge: 'bg-slate-500/10 text-slate-500',
};

const categoryLabels: Record<string, string> = {
  meal_rate: 'Meal Rate',
  meal_plan_supplement: 'Meal Supplement',
  extra_person_charge: 'Extra Person',
  extra_bed_charge: 'Extra Bed',
  child_rate: 'Child Rate',
  other_charge: 'Other Charge',
};

export default function PriceItemsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const data = await getPriceItems(search || undefined);
        setItems(data);
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
          <h2 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-3">
             <Package className="text-accent" />
             Price Items & Supplements
          </h2>
          <p className="text-muted-foreground text-sm">Granular pricing data for supplements, ages, and extra charges</p>
        </div>
        <div className="glass px-6 py-3 rounded-xl text-sm font-medium flex items-center gap-2">
           <Layers className="text-accent" size={16} />
           <span>{items.length} Total Items</span>
        </div>
      </header>

      <div className="relative group max-w-2xl">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-accent transition-colors" size={18} />
        <input 
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by hotel or description..."
          className="w-full bg-card border border-card-border rounded-2xl pl-12 pr-6 py-4 focus:outline-none focus:border-accent/40 focus:ring-4 ring-accent/5 transition-all text-sm"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {loading ? (
          [1,2,3,4,5,6].map(i => (
            <div key={i} className="glass-card h-64 rounded-3xl animate-pulse" />
          ))
        ) : items.length === 0 ? (
          <div className="col-span-full py-20 text-center glass-card rounded-3xl">
             <p className="text-muted-foreground">No supplemental items found.</p>
          </div>
        ) : items.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card p-6 rounded-[2rem] flex flex-col justify-between group hover:border-accent/30 transition-all"
          >
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${categoryColors[item.category] || categoryColors.other_charge}`}>
                   {categoryLabels[item.category] || item.category}
                </div>
                <button className="text-muted-foreground hover:text-foreground transition-colors">
                   <ArrowUpRight size={18} />
                </button>
              </div>

              <div>
                 <h4 className="text-lg font-bold truncate group-hover:text-accent transition-colors">{item.hotel_name}</h4>
                 <p className="text-sm text-neutral-400 line-clamp-2 mt-1 leading-relaxed">
                    {item.description}
                 </p>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
                     <p className="text-[10px] text-muted-foreground uppercase font-bold mb-1">Per Unit</p>
                     <p className="text-xs font-semibold">{item.per_unit || 'N/A'}</p>
                  </div>
                  <div className="p-3 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
                     <p className="text-[10px] text-muted-foreground uppercase font-bold mb-1">Target</p>
                     <p className="text-xs font-semibold truncate">{item.adult_or_child || 'All'}</p>
                  </div>
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-white/[0.05] flex justify-between items-end">
               <div>
                  <div className="flex items-center gap-1 text-[10px] font-bold text-accent uppercase mb-1">
                     <CreditCard size={10} />
                     Base Price
                  </div>
                  <p className="text-2xl font-black font-mono tracking-tight">
                    <span className="text-sm text-muted-foreground mr-1 font-sans font-bold">{item.currency}</span>
                    {item.price}
                  </p>
               </div>
               <div className="flex items-center gap-2 text-[10px] text-neutral-500 font-bold uppercase">
                  <Calendar size={12} className="text-accent/40" />
                  {item.applicable_dates || 'All Seasons'}
               </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
