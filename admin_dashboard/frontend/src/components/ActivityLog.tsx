"use client";

import { useEffect, useState } from "react";
import { Activity, Database, Cloud, AlertCircle, CheckCircle, XCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { getAuditLog, getSystemStatus } from "@/services/api";

interface AuditEvent {
  timestamp: string;
  event_type: string;
  details: string;
  data_source: string;
}

interface SystemStatus {
  airtable: { status: string; enabled: boolean };
  sqlite: { status: string; enabled: boolean };
  active_source: string;
  timestamp: string;
}

export default function ActivityLog() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Shared API client: correct base URL and auth header
        const [audit, status] = await Promise.all([
          getAuditLog(20),
          getSystemStatus(),
        ]);

        setEvents(audit);
        setSystemStatus(status);
      } catch (err) {
        console.error("Failed to fetch activity data", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const getSourceIcon = (source: string) => {
    if (source === "airtable") return Cloud;
    if (source === "sqlite") return Database;
    return AlertCircle;
  };

  const getSourceColor = (source: string) => {
    if (source === "airtable") return "text-blue-500 bg-blue-500/10";
    if (source === "sqlite") return "text-emerald-500 bg-emerald-500/10";
    return "text-yellow-500 bg-yellow-500/10";
  };

  return (
    <div className="space-y-6">
      {/* System Status Banner */}
      {systemStatus && (
        <div className="glass-card p-4 rounded-2xl">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Activity className="text-accent" size={18} />
              <span className="font-bold text-sm">System Status</span>
            </div>
            <div className={`px-3 py-1 rounded-full text-[10px] font-bold ${getSourceColor(systemStatus.active_source)}`}>
              ACTIVE: {systemStatus.active_source.toUpperCase()}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-3">
            {/* Airtable Status */}
            <div className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.02]">
              <Cloud size={14} className={systemStatus.airtable.status === "connected" ? "text-blue-500" : "text-gray-500"} />
              <div className="flex-1">
                <div className="text-[10px] font-bold text-muted-foreground">Airtable</div>
                <div className="text-xs font-semibold flex items-center gap-1">
                  {systemStatus.airtable.status === "connected" ? (
                    <><CheckCircle size={10} className="text-emerald-500" /> Connected</>
                  ) : (
                    <><XCircle size={10} className="text-red-500" /> Offline</>
                  )}
                </div>
              </div>
            </div>
            
            {/* SQLite Status */}
            <div className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.02]">
              <Database size={14} className={systemStatus.sqlite.status === "connected" ? "text-emerald-500" : "text-gray-500"} />
              <div className="flex-1">
                <div className="text-[10px] font-bold text-muted-foreground">SQLite</div>
                <div className="text-xs font-semibold flex items-center gap-1">
                  {systemStatus.sqlite.status === "connected" ? (
                    <><CheckCircle size={10} className="text-emerald-500" /> Connected</>
                  ) : (
                    <><XCircle size={10} className="text-red-500" /> Offline</>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Activity Log */}
      <div className="glass-card rounded-3xl overflow-hidden">
        <div className="p-4 border-b border-card-border bg-white/[0.01]">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <Activity size={18} className="text-accent" />
            Live Activity
          </h3>
          <p className="text-[10px] text-muted-foreground mt-1">
            Real-time operations • Auto-refresh every 5s
          </p>
        </div>
        
        <div className="max-h-80 overflow-y-auto">
          <AnimatePresence>
            {events.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground text-xs">
                No activity yet
              </div>
            ) : (
              events.map((event, i) => {
                const SourceIcon = getSourceIcon(event.data_source);
                return (
                  <motion.div
                    key={`${event.timestamp}-${i}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-3 border-b border-card-border hover:bg-white/[0.02] transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-1.5 rounded-lg ${getSourceColor(event.data_source)}`}>
                        <SourceIcon size={12} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-[11px] font-bold text-accent">
                            {event.event_type.replace(/_/g, " ").toUpperCase()}
                          </span>
                          <span className="text-[9px] text-muted-foreground">
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-[10px] text-muted-foreground truncate">
                          {event.details}
                        </p>
                      </div>
                      <div className={`px-2 py-0.5 rounded text-[8px] font-bold ${getSourceColor(event.data_source)}`}>
                        {event.data_source.toUpperCase()}
                      </div>
                    </div>
                  </motion.div>
                );
              })
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
