'use client';

import { AuditSummary } from '@/lib/types';
import { motion } from 'framer-motion';
import { Layers, ShieldCheck, Zap, Activity } from 'lucide-react';

interface CoverageComparatorProps {
  summary: AuditSummary;
}

export function CoverageComparator({ summary }: CoverageComparatorProps) {
  const comparator = summary.coverage_comparator || {
    axe_only_found: summary.total_issues,
    advanced_found: 0,
    axe_coverage_percent: 100
  };

  const data = [
    { 
      label: 'Deterministic (Axe)', 
      value: comparator.axe_only_found, 
      color: 'bg-indigo-500', 
      icon: <ShieldCheck size={16} />,
      desc: 'Standard WCAG rules and best practices'
    },
    { 
      label: 'Advanced & AI', 
      value: comparator.advanced_found, 
      color: 'bg-brand-500', 
      icon: <Zap size={16} />,
      desc: 'Heuristic, structural and visual analysis'
    }
  ];

  const total = comparator.axe_only_found + comparator.advanced_found;

  return (
    <div className="glass-card p-8 border-slate-800 h-full">
      <div className="flex items-center gap-2 text-slate-500 mb-8">
        <Activity size={18} />
        <h2 className="text-sm font-black uppercase tracking-widest">Engine Coverage Delta</h2>
      </div>

      <div className="space-y-12">
        {data.map((item, index) => {
          const percentage = total > 0 ? (item.value / total) * 100 : 0;
          
          return (
            <div key={item.label} className="relative">
              <div className="flex justify-between items-end mb-4">
                <div>
                  <div className="flex items-center gap-2 text-white font-bold mb-1">
                    {item.icon}
                    <span>{item.label}</span>
                  </div>
                  <p className="text-[10px] uppercase font-black tracking-tighter text-slate-600">{item.desc}</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-black text-white leading-none">{item.value}</div>
                  <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Detections</div>
                </div>
              </div>
              
              <div className="h-3 w-full bg-slate-900 rounded-full overflow-hidden border border-white/5">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ duration: 1, delay: index * 0.2 }}
                  className={`h-full ${item.color} shadow-[0_0_15px_rgba(var(--brand-500),0.4)]`}
                />
              </div>
            </div>
          );
        })}

        <div className="mt-8 p-6 bg-slate-950 rounded-2xl border border-slate-900 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-20 transition-opacity">
            <Layers size={80} />
          </div>
          <div className="relative z-10">
            <div className="text-[10px] font-black uppercase tracking-[0.2em] text-brand-400 mb-2">Synthesis Accuracy</div>
            <div className="text-3xl font-black text-white mb-2">{comparator.axe_coverage_percent}%</div>
            <p className="text-xs text-slate-500 leading-relaxed max-w-[240px]">
              Advanced engines identified <span className="text-brand-400">+{comparator.advanced_found}</span> additional barriers beyond standard deterministic rules.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
