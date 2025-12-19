"use client";

import React from 'react';
import { User, Mail, Shield, Bell, Lock } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="space-y-8">
      <header>
        <h2 className="text-3xl font-bold tracking-tight mb-2">Settings</h2>
        <p className="text-muted-foreground text-sm">Manage your account and application preferences</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Section */}
        <div className="glass-card p-6 rounded-[2rem] space-y-6">
          <div className="flex flex-col items-center text-center pb-6 border-b border-white/[0.05]">
            <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-accent to-violet-500 mb-4 shadow-lg shadow-accent/20 flex items-center justify-center text-3xl font-bold text-white">
              M
            </div>
            <h3 className="text-xl font-bold">Maahela</h3>
            <p className="text-sm text-muted-foreground">maahela@jake.io</p>
            <span className="mt-3 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-xs font-bold border border-emerald-500/20">
              Admin Access
            </span>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03]">
              <div className="p-2 rounded-lg bg-white/[0.05]">
                <User size={18} className="text-muted-foreground" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-bold text-muted-foreground uppercase">Role</p>
                <p className="text-sm font-medium">Super Admin</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03]">
              <div className="p-2 rounded-lg bg-white/[0.05]">
                <Mail size={18} className="text-muted-foreground" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-bold text-muted-foreground uppercase">Email</p>
                <p className="text-sm font-medium">maahela@jake.io</p>
              </div>
            </div>
          </div>
        </div>

        {/* Settings Options (Placeholder) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 rounded-[2rem] space-y-6">
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Shield size={20} className="text-accent" />
              Security & Privacy
            </h3>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-xl bg-white/[0.05]">
                    <Lock size={18} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm">Two-Factor Authentication</h4>
                    <p className="text-xs text-muted-foreground">Add an extra layer of security to your account</p>
                  </div>
                </div>
                <button className="px-4 py-2 rounded-xl bg-white/[0.05] text-xs font-bold hover:bg-white/10 transition-colors">
                  Enable
                </button>
              </div>

              <div className="flex justify-between items-center p-4 rounded-2xl bg-white/[0.02] border border-white/[0.05]">
                <div className="flex items-center gap-4">
                  <div className="p-2 rounded-xl bg-white/[0.05]">
                    <Bell size={18} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm">Notifications</h4>
                    <p className="text-xs text-muted-foreground">Manage email and push notifications</p>
                  </div>
                </div>
                <button className="px-4 py-2 rounded-xl bg-white/[0.05] text-xs font-bold hover:bg-white/10 transition-colors">
                  Configure
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
