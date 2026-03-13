'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { toast } from 'react-hot-toast';
import { 
  BarChart3, 
  ShieldCheck, 
  Zap, 
  Clock, 
  Sparkles,
  Database
} from 'lucide-react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { AuditForm } from '@/components/audit/AuditForm';
import { FeatureCard } from '@/components/audit/FeatureCard';
import { Engine } from '@/lib/types';

export default function HomePage() {
  const [url, setUrl] = useState('');
  const router = useRouter();

  const { data: engines, isLoading: enginesLoading } = useQuery<Engine[]>({
    queryKey: ['engines'],
    queryFn: api.getEngines,
  });

  const startAudit = useMutation({
    mutationFn: (request: { url: string, engines: string[], enable_ai: boolean }) => 
      api.startAudit(request),
    onSuccess: (data) => {
      toast.success('Audit started! Redirecting...');
      router.push(`/audit/${data.audit_id}`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  const handleStartAudit = (url: string, options: { engines: string[], enableAI: boolean }) => {
    if (!url) {
      toast.error('Please enter a URL');
      return;
    }
    
    try {
      new URL(url);
    } catch {
      toast.error('Please enter a valid URL (include http:// or https://)');
      return;
    }
    
    startAudit.mutate({ 
      url, 
      engines: options.engines, 
      enable_ai: options.enableAI 
    });
  };

  return (
    <main className="min-h-screen relative overflow-hidden bg-slate-950 selection:bg-brand-500/30">
      {/* Dynamic Background Elements */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-brand-600/20 rounded-full blur-[120px] -z-10 animate-pulse"></div>
      <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-indigo-600/10 rounded-full blur-[100px] -z-10 delay-1000 animate-pulse"></div>

      <div className="container-custom pt-32 pb-24">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-900/50 border border-slate-800 text-brand-400 text-sm font-bold mb-8 shadow-xl">
            <Sparkles size={16} />
            <span className="uppercase tracking-widest">Next-Gen Accessibility Engine</span>
          </div>
          
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-6 text-gradient">
            AccessLens
          </h1>
          
          <p className="text-xl md:text-2xl text-slate-400 max-w-3xl mx-auto mb-12 font-medium leading-relaxed">
            Eliminate barriers with multi-engine intelligence. 
            Automated <span className="text-white">WCAG compliance</span> auditing powered by Playwright and AI vision.
          </p>
          
          <div className="flex flex-col items-center gap-6">
            <AuditForm
              url={url}
              setUrl={setUrl}
              onStartAudit={handleStartAudit}
              isLoading={startAudit.isPending}
              engines={engines}
            />
            
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1 }}
              className="flex items-center gap-4"
            >
              <Link 
                href="/dashboard" 
                className="flex items-center gap-2 text-slate-500 hover:text-brand-400 transition-colors text-xs font-black uppercase tracking-widest"
              >
                <Database size={14} />
                Access Intelligence Dashboard
              </Link>
            </motion.div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-32">
          <FeatureCard 
            icon={<ShieldCheck className="text-brand-500" />}
            title="Policy Enforcement"
            description="Automated WCAG 2.1/2.2 A-AAA rule validation with zero false positives."
            delay={0.2}
          />
          <FeatureCard 
            icon={<Zap className="text-brand-500" />}
            title="Instant Synthesis"
            description="Parallel engine processing provides comprehensive results in under 60 seconds."
            delay={0.3}
          />
          <FeatureCard 
            icon={<BarChart3 className="text-brand-500" />}
            title="Visual Intelligence"
            description="Heatmaps and confidence scoring powered by next-gen computer vision."
            delay={0.4}
          />
        </div>
      </div>
    </main>
  );
}

