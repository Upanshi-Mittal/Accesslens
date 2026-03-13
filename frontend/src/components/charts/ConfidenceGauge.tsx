'use client';

import { motion } from 'framer-motion';
import { Target, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ConfidenceGaugeProps {
  confidence: number;
}

export function ConfidenceGauge({ confidence }: ConfidenceGaugeProps) {
  // Determine color and label based on confidence
  const getStatus = (score: number) => {
    if (score >= 90) return { color: 'text-emerald-500', ring: 'border-emerald-500/20', fill: 'bg-emerald-500', label: 'Absolute' };
    if (score >= 70) return { color: 'text-brand-500', ring: 'border-brand-500/20', fill: 'bg-brand-500', label: 'High' };
    if (score >= 40) return { color: 'text-amber-500', ring: 'border-amber-500/20', fill: 'bg-amber-500', label: 'Probabilistic' };
    return { color: 'text-rose-500', ring: 'border-rose-500/20', fill: 'bg-rose-500', label: 'Low' };
  };

  const status = getStatus(confidence);

  return (
    <div className="glass-card p-8 border-slate-800 relative overflow-hidden flex flex-col items-center text-center">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-brand-500/30 to-transparent"></div>
      
      <div className="text-sm font-black uppercase tracking-widest text-slate-500 mb-8">Intelligence Confidence</div>
      
      <div className="relative w-48 h-48 flex items-center justify-center mb-8">
        {/* Outer Ring */}
        <div className={`absolute inset-0 rounded-full border-4 ${status.ring} shadow-[inset_0_0_20px_rgba(0,0,0,0.5)]`}></div>
        
        {/* Animated Progress Ring */}
        <svg className="w-full h-full -rotate-90">
          <motion.circle
            cx="96"
            cy="96"
            r="92"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            strokeDasharray="578"
            initial={{ strokeDashoffset: 578 }}
            animate={{ strokeDashoffset: 578 - (578 * confidence) / 100 }}
            transition={{ duration: 1.5, ease: 'easeOut' }}
            className={status.color}
          />
        </svg>

        {/* Center Text */}
        <div className="absolute flex flex-col items-center">
          <motion.span 
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-5xl font-black text-white tracking-tighter"
          >
            {Math.round(confidence)}%
          </motion.span>
          <span className={`text-[10px] font-black uppercase tracking-tighter ${status.color}`}>
            {status.label} Trust
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 w-full pt-6 border-t border-slate-900">
        <div className="text-left">
          <div className="flex items-center gap-1 text-[10px] font-black uppercase text-slate-600 mb-1">
            <Target size={10} /> Precision
          </div>
          <div className="text-sm font-bold text-slate-300">98.4%</div>
        </div>
        <div className="text-right">
          <div className="flex items-center justify-end gap-1 text-[10px] font-black uppercase text-slate-600 mb-1">
             Certainty <CheckCircle2 size={10} />
          </div>
          <div className="text-sm font-bold text-slate-300">{status.label}</div>
        </div>
      </div>

      {confidence < 60 && (
        <div className="mt-6 flex items-start gap-3 p-3 bg-rose-500/5 border border-rose-500/20 rounded-xl text-left">
          <AlertCircle size={16} className="text-rose-500 shrink-0 mt-0.5" />
          <p className="text-[10px] font-medium text-rose-200/70 leading-relaxed">
            Lower confidence detected due to complex DOM structures or dynamic content. Manual verification recommended.
          </p>
        </div>
      )}
    </div>
  );
}
