'use client';

import { UnifiedIssue } from '@/lib/types';
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { Target, AlertCircle, Info } from 'lucide-react';

interface HeatmapOverlayProps {
  issues: UnifiedIssue[];
  screenshot?: string;
  viewportWidth?: number;
}

export function HeatmapOverlay({ issues, screenshot, viewportWidth = 1280 }: HeatmapOverlayProps) {
  const [hoveredIssue, setHoveredIssue] = useState<UnifiedIssue | null>(null);

  const locatableIssues = issues.filter(i => i.location?.bounding_box);

  if (!screenshot && locatableIssues.length === 0) {
    return (
      <div className="glass-card p-20 text-center border-slate-800">
        <Target size={48} className="mx-auto text-slate-800 mb-4" />
        <p className="text-slate-500 font-medium">No spatial data available for heatmap visualization.</p>
      </div>
    );
  }

  return (
    <div className="relative glass-card border-slate-800 overflow-hidden bg-slate-900 shadow-2xl">
      <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/50">
        <div className="flex items-center gap-2">
          <Target size={16} className="text-brand-400" />
          <h2 className="text-xs font-black uppercase tracking-widest text-slate-400">Spatial Distribution Map</h2>
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500">
            <div className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_5px_rgba(244,63,94,0.5)]"></div>
            <span>Critical Density</span>
          </div>
          <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500">
            <div className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_5px_rgba(245,158,11,0.5)]"></div>
            <span>High Awareness</span>
          </div>
        </div>
      </div>

      <div className="relative overflow-auto max-h-[700px] border-t border-slate-800 bg-slate-950">
        <div className="relative mx-auto" style={{ width: '100%', maxWidth: '1280px' }}>
          {screenshot ? (
            <img 
              src={`data:image/jpeg;base64,${screenshot}`} 
              alt="Page Scan" 
              className="w-full h-auto opacity-40 brightness-50"
            />
          ) : (
             <div className="w-full aspect-video bg-slate-900 flex items-center justify-center">
               <span className="text-slate-800 font-black text-4xl uppercase tracking-tighter italic">Scanning...</span>
             </div>
          )}

          {/* Issue Markers */}
          {locatableIssues.map((issue) => {
            const box = issue.location?.bounding_box;
            if (!box) return null;

            const severityColor = {
              critical: 'bg-rose-500',
              serious: 'bg-orange-500',
              moderate: 'bg-amber-500',
              minor: 'bg-blue-500'
            }[issue.severity];

            return (
              <motion.div
                key={issue.id}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 0.8 }}
                whileHover={{ scale: 1.5, opacity: 1, zIndex: 50 }}
                className={`absolute rounded-full cursor-pointer border-2 border-white/20 shadow-lg ${severityColor}`}
                style={{
                  left: `${(box.x / viewportWidth) * 100}%`,
                  top: `${box.y}px`, 
                  width: '24px',
                  height: '24px',
                  transform: 'translate(-50%, -50%)'
                }}
                onMouseEnter={() => setHoveredIssue(issue)}
                onMouseLeave={() => setHoveredIssue(null)}
              />
            );
          })}

          {/* Hover Portal */}
          <AnimatePresence>
            {hoveredIssue && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 10 }}
                className="fixed bottom-12 left-1/2 -translate-x-1/2 z-[100] w-96 glass-card p-6 border-brand-500/50 shadow-[0_0_40px_rgba(var(--brand-500),0.2)]"
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg bg-orange-500/10 text-orange-500`}>
                    <AlertCircle size={20} />
                  </div>
                  <div>
                    <h3 className="text-white font-black text-sm mb-1">{hoveredIssue.title}</h3>
                    <p className="text-slate-400 text-xs leading-relaxed line-clamp-2">{hoveredIssue.description}</p>
                    <div className="mt-3 flex items-center gap-2">
                       <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-slate-400">
                         {hoveredIssue.severity}
                       </span>
                       <span className="text-[10px] font-bold text-slate-600">
                         SEL: {hoveredIssue.location?.selector.split('>').pop()?.trim()}
                       </span>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
      
      <div className="p-4 bg-slate-950 border-t border-slate-900 flex items-center gap-2">
        <Info size={14} className="text-slate-600" />
        <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">
          Interactive distribution map based on engine-computed bounding boxes.
        </span>
      </div>
    </div>
  );
}
