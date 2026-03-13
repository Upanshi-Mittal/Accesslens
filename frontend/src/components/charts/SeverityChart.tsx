import { IssueSeverity } from '@/lib/types';
import { motion } from 'framer-motion';

interface SeverityChartProps {
  data: Record<IssueSeverity, number>;
}

export function SeverityChart({ data }: SeverityChartProps) {
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  
  const severityConfig = {
    critical: { color: 'bg-rose-500', barCol: 'from-rose-500 to-rose-600', label: 'Critical' },
    serious: { color: 'bg-orange-500', barCol: 'from-orange-500 to-orange-600', label: 'Serious' },
    moderate: { color: 'bg-amber-500', barCol: 'from-amber-500 to-amber-600', label: 'Moderate' },
    minor: { color: 'bg-blue-500', barCol: 'from-blue-500 to-indigo-600', label: 'Minor' },
  };

  return (
    <div className="glass-card p-8 border-slate-800">
      <h2 className="text-sm font-black uppercase tracking-widest text-slate-500 mb-8">Intensity Distribution</h2>
      
      {total === 0 ? (
        <div className="text-center py-12 flex flex-col items-center gap-4">
           <div className="w-12 h-12 bg-slate-900 rounded-full flex items-center justify-center text-slate-700">
             <div className="w-4 h-4 rounded-full border-2 border-current"></div>
           </div>
           <p className="text-slate-600 text-xs font-bold uppercase tracking-widest">No signals detected</p>
        </div>
      ) : (
        <div className="space-y-6">
          {(Object.entries(severityConfig) as [IssueSeverity, typeof severityConfig.critical][]).map(([severity, config]) => {
            const count = data[severity] || 0;
            const percentage = total > 0 ? (count / total) * 100 : 0;
            
            return (
              <div key={severity} className="group">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-xs font-black uppercase tracking-widest text-slate-400 group-hover:text-white transition-colors">{config.label}</span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-lg font-black text-white leading-none">{count}</span>
                    <span className="text-[10px] font-bold text-slate-600 uppercase">{percentage.toFixed(0)}%</span>
                  </div>
                </div>
                <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-white/5 shadow-inner">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className={`h-full rounded-full bg-gradient-to-r ${config.barCol} shadow-[0_0_10px_rgba(var(--brand-500),0.3)]`}
                  />
                </div>
              </div>
            );
          })}
          
          <div className="mt-8 pt-6 border-t border-slate-900 flex justify-between items-center">
             <span className="text-[10px] font-black tracking-widest text-slate-600 uppercase">Aggregated Density</span>
             <span className="text-sm font-black text-slate-400">{total} Issues Found</span>
          </div>
        </div>
      )}
    </div>
  );
}
