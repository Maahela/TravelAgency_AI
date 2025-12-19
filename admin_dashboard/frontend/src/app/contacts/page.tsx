
"use client";

import React, { useEffect, useState } from 'react';
import { 
  Search, 
  RefreshCcw,
  Globe,
  Mail,
  User,
  History,
  ChevronRight,
  ChevronLeft
} from 'lucide-react';
import { motion } from 'framer-motion';
import { getContacts } from '@/services/api';
import { Skeleton } from '@/components/ui/Skeleton';

interface HotelContact {
  id: number;
  name: string;
  email_address?: string;
  website?: string;
  contact_person?: string;
  last_rate_request_date?: string;
  created_at: string;
  updated_at: string;
}

export default function ContactsPage() {
  const [contacts, setContacts] = useState<HotelContact[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const data = await getContacts();
        setContacts(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const filteredContacts = contacts.filter(contact => 
    contact.name.toLowerCase().includes(search.toLowerCase()) ||
    contact.email_address?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8">
      <header className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold tracking-tight mb-2">Hotel Contacts</h2>
          <p className="text-muted-foreground text-sm">Directory of hotel properties and contact details</p>
        </div>
        <button 
          onClick={() => {
            setLoading(true);
            getContacts().then(setContacts).finally(() => setLoading(false));
          }}
          className="glass p-3 rounded-xl hover:bg-white/[0.05] transition-colors"
        >
          <RefreshCcw size={18} className={loading ? 'animate-spin' : ''} />
        </button>
      </header>

      <div className="flex gap-4">
        <div className="flex-1 relative group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-accent transition-colors" size={18} />
          <input 
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search hotels by name or email..."
            className="w-full bg-card border border-card-border rounded-2xl pl-12 pr-6 py-4 focus:outline-none focus:border-accent/40 focus:ring-4 ring-accent/5 transition-all text-sm"
          />
        </div>
      </div>

      <div className="glass-card rounded-[2.5rem] overflow-hidden border border-white/[0.05]">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/[0.05] bg-white/[0.01]">
                <th className="px-8 py-5 text-xs font-bold uppercase tracking-wider text-muted-foreground">Hotel Name</th>
                <th className="px-8 py-5 text-xs font-bold uppercase tracking-wider text-muted-foreground">Contact Info</th>
                <th className="px-8 py-5 text-xs font-bold uppercase tracking-wider text-muted-foreground">Details</th>
                <th className="px-8 py-5 text-xs font-bold uppercase tracking-wider text-muted-foreground text-right">Last Interaction</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.03]">
              {loading ? (
                // Skeleton Loading State
                [1, 2, 3, 4, 5].map((i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-8 py-6">
                      <div className="flex items-center gap-4">
                        <Skeleton className="w-10 h-10 rounded-xl" />
                        <div className="space-y-2">
                          <Skeleton className="h-4 w-32" />
                          <Skeleton className="h-3 w-24" />
                        </div>
                      </div>
                    </td>
                    <td className="px-8 py-6">
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-40" />
                        <Skeleton className="h-3 w-28" />
                      </div>
                    </td>
                    <td className="px-8 py-6">
                       <Skeleton className="h-6 w-16 rounded-lg" />
                    </td>
                    <td className="px-8 py-6 text-right">
                      <div className="flex flex-col items-end gap-1">
                        <Skeleton className="h-3 w-20" />
                      </div>
                    </td>
                  </tr>
                ))
              ) : filteredContacts.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-8 py-20 text-center text-muted-foreground">
                    No contacts found matching your search.
                  </td>
                </tr>
              ) : filteredContacts.map((contact, i) => (
                <motion.tr 
                  key={contact.id} 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="hover:bg-white/[0.02] transition-colors group"
                >
                  <td className="px-8 py-6">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center text-accent">
                         <span className="font-bold text-lg">{contact.name.charAt(0)}</span>
                      </div>
                      <div>
                        <p className="font-bold text-sm tracking-tight group-hover:text-accent transition-colors">
                          {contact.name}
                        </p>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <Globe size={10} className="text-muted-foreground" />
                          <p className="text-[10px] text-muted-foreground truncate max-w-[150px]">
                            {contact.website || 'No website'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-2">
                        <Mail size={12} className="text-accent/60" />
                        <p className="text-sm font-medium">{contact.email_address || 'N/A'}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <User size={12} className="text-accent/60" />
                        <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">
                          {contact.contact_person || 'No contact person'}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-8 py-6">
                     <span className="text-[10px] bg-white/[0.05] px-2 py-1 rounded-lg text-muted-foreground border border-white/[0.05]">
                        ID: {contact.id}
                     </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <div className="flex flex-col items-end gap-1">
                      <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-bold uppercase tracking-wider">
                        <History size={12} className="text-accent/60" />
                        {contact.last_rate_request_date || 'Never'}
                      </div>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-8 py-5 border-t border-white/[0.05] flex justify-between items-center text-sm text-muted-foreground bg-white/[0.01]">
          <p>Showing <span className="text-foreground font-bold">{filteredContacts.length}</span> properties</p>
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
    </div>
  );
}
