'use client';

import { useState } from 'react';
import { UnifiedIssue } from '@/lib/types';
import { SeverityBadge } from './SeverityBadge';
import { ChevronDown, ChevronUp, Code, MapPin, ExternalLink, Info, Terminal } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface IssueCardProps {
  issue: UnifiedIssue;
}

export function IssueCard({ issue }: IssueCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div 
      layout
      className={`glass-card mb-4 overflow-hidden border-slate-800 transition-all duration-300 ${expanded ? 'ring-1 ring-brand-500/30 shadow-brand-500/5' : ''}`}
    >
      <div
        className="p-5 cursor-pointer flex items-start justify-between group"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            <SeverityBadge severity={issue.severity} />
            <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md border border-slate-800 bg-slate-900 text-slate-400">
              {issue.engine_name.replace(/_/g, ' ')}
            </span>
            <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-700"></span>
              Confidence: {issue.confidence_score}%
            </div>
          </div>
          <h3 className="text-lg font-bold text-white group-hover:text-brand-400 transition-colors leading-tight">{issue.title}</h3>
        </div>
        <div className={`ml-4 p-2 rounded-lg transition-colors ${expanded ? 'bg-brand-500 text-white' : 'bg-slate-900 text-slate-600 group-hover:text-slate-400'}`}>
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-6 pt-2 border-t border-slate-800 bg-slate-900/40">
              <p className="text-slate-300 mb-6 text-sm leading-relaxed font-medium">{issue.description}</p>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-6">
                  {issue.wcag_criteria.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-xs font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
                        <Info size={14} /> Standards Compliance
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {issue.wcag_criteria.map((criteria) => (
                          <a
                            key={criteria.id}
                            href={criteria.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-900 border border-slate-800 text-slate-300 rounded-lg text-xs font-bold hover:border-brand-500/50 hover:text-brand-400 transition-all hover:shadow-[0_0_10px_rgba(var(--brand-500),0.1)]"
                          >
                            <span>{criteria.id} ({criteria.level})</span>
                            <ExternalLink size={12} className="opacity-50" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {issue.location && (
                    <div className="space-y-3">
                      <h4 className="text-xs font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
                        <MapPin size={14} /> Affected Element
                      </h4>
                      <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 shadow-inner">
                        <code className="text-xs text-brand-400 font-mono break-all whitespace-pre-wrap leading-relaxed">
                          {issue.location.selector}
                        </code>
                        {issue.location.html && (
                          <div className="mt-4 pt-4 border-t border-slate-900">
                             <p className="text-[10px] font-black uppercase text-slate-600 mb-2">Original Snippet</p>
                             <div className="relative group">
                               <pre className="text-xs bg-black/40 p-4 rounded-lg overflow-x-auto text-slate-400 border border-slate-800/50">
                                <code className="font-mono">{issue.location.html}</code>
                              </pre>
                             </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <div className="space-y-6">
                  {issue.remediation && (
                    <div className="space-y-3">
                      <h4 className="text-xs font-black uppercase tracking-widest text-emerald-500 flex items-center gap-2">
                        <Code size={14} /> Solution Strategy
                      </h4>
                      <div className="bg-emerald-500/5 rounded-2xl border border-emerald-500/20 p-5 shadow-inner">
                        <p className="text-sm text-slate-200 mb-4 font-semibold leading-relaxed">
                          {issue.remediation.description}
                        </p>
                        {issue.remediation.code_after && (
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                               <span className="text-[10px] font-black uppercase text-emerald-600 tracking-widest flex items-center gap-1.5">
                                 <Terminal size={12} /> Refactored Code
                               </span>
                            </div>
                            <div className="relative">
                              <pre className="text-xs bg-slate-950 p-5 rounded-xl border border-emerald-500/30 text-emerald-300 overflow-x-auto shadow-2xl">
                                <code className="font-mono whitespace-pre-wrap">{issue.remediation.code_after}</code>
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-tighter text-slate-600 mt-8 pt-4 border-t border-slate-800">
                <div className="flex gap-4">
                  <span>ID: {issue.id.slice(0, 12)}</span>
                  <span>Type: {issue.issue_type}</span>
                </div>
                {issue.tags.length > 0 && (
                  <div className="flex gap-2">
                    {issue.tags.slice(0, 3).map(tag => (
                      <span key={tag} className="px-1.5 py-0.5 bg-slate-900 rounded border border-slate-800">#{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
