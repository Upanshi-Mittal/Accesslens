'use client';

import { UnifiedIssue } from '@/lib/types';
import { IssueCard } from './IssueCard';
import { motion, AnimatePresence } from 'framer-motion';
import { Search } from 'lucide-react';

interface IssueListProps {
  issues: UnifiedIssue[];
  filter?: (issue: UnifiedIssue) => boolean;
}

export function IssueList({ issues, filter }: IssueListProps) {
  const filteredIssues = filter ? issues.filter(filter) : issues;

  if (filteredIssues.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-20 glass-card bg-emerald-500/5 border-emerald-500/20"
      >
        <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-500 mx-auto mb-6">
          <Search size={32} />
        </div>
        <h3 className="text-xl font-bold text-white mb-2">Pristine Architecture</h3>
        <p className="text-slate-400 font-medium max-w-xs mx-auto">No accessibility barriers were detected by the active engines. Great job!</p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-4">
      <AnimatePresence>
        {filteredIssues.map((issue, index) => (
          <motion.div
            key={issue.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <IssueCard issue={issue} />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
