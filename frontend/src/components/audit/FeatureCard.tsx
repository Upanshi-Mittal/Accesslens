'use client';

import { motion } from 'framer-motion';
import React from 'react';

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay?: number;
}

export function FeatureCard({ icon, title, description, delay = 0 }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay }}
      className="glass-card p-10 border-slate-800 hover:border-brand-500/50 transition-colors group relative overflow-hidden"
    >
      <div className="absolute -right-8 -bottom-8 opacity-5 group-hover:opacity-10 transition-opacity">
        {icon}
      </div>
      
      <div className="mb-6 p-4 rounded-2xl bg-slate-900 w-fit group-hover:bg-brand-500/10 transition-colors">
        {icon}
      </div>
      
      <h3 className="text-xl font-black text-white mb-4 italic uppercase tracking-tighter">{title}</h3>
      <p className="text-slate-400 font-medium leading-relaxed">{description}</p>
    </motion.div>
  );
}
