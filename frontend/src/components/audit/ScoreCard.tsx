'use client';

import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';
import React from 'react';

interface ScoreCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: string;
  subtitle?: string;
  color?: string;
}

export function ScoreCard({ title, value, icon, trend, subtitle, color }: ScoreCardProps) {
  const bgColor = color || 'from-brand-500/20 to-indigo-500/20';

  return (
    <motion.div
      whileHover={{ y: -5, scale: 1.02 }}
      className={`relative glass-card p-6 overflow-hidden group border-slate-800`}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${bgColor} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
      
      <div className="relative z-10">
        <div className="flex justify-between items-start mb-4">
          <div className="p-2 rounded-lg bg-slate-900 group-hover:bg-slate-800 transition-colors">
            {icon}
          </div>
          {trend && (
            <span className="text-[10px] font-black text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              {trend}
            </span>
          )}
        </div>
        
        <div className="space-y-1">
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-500 group-hover:text-slate-400 transition-colors">
            {title}
          </h3>
          <div className="text-3xl font-black text-white tracking-tighter">
            {value}
          </div>
          {subtitle && (
            <p className="text-[10px] font-bold text-slate-600 uppercase tracking-tight">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div className="absolute bottom-0 left-0 h-1 bg-gradient-to-r from-transparent via-brand-500/50 to-transparent w-full opacity-0 group-hover:opacity-100 transition-opacity" />
    </motion.div>
  );
}
