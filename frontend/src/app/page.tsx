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
  Sparkles,
  Database,
} from 'lucide-react';

import Link from 'next/link';
import { motion } from 'framer-motion';

import { AuditForm } from '@/components/audit/AuditForm';
import { FeatureCard } from '@/components/audit/FeatureCard';
import { Engine } from '@/lib/types';

export default function HomePage() {
  const [url, setUrl] = useState('');
  const router = useRouter();

  const { data: engines } = useQuery<Engine[]>({
    queryKey: ['engines'],
    queryFn: api.getEngines,
  });

  const startAudit = useMutation({
    mutationFn: (request: {
      url: string;
      engines: string[];
      enable_ai: boolean;
    }) => api.startAudit(request),

    onSuccess: (data) => {
      toast.success('Audit started');
      router.push(`/audit/${data.audit_id}`);
    },

    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  const handleStartAudit = (
    url: string,
    options: { engines: string[]; enableAI: boolean }
  ) => {
    if (!url) {
      toast.error('Enter URL');
      return;
    }

    startAudit.mutate({
      url,
      engines: options.engines,
      enable_ai: options.enableAI,
    });
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-start">

      {/* Background glow */}
      <div className="absolute top-0 left-1/3 w-[500px] h-[500px] bg-blue-600/20 blur-[120px] rounded-full -z-10" />
      <div className="absolute bottom-0 right-1/3 w-[400px] h-[400px] bg-indigo-600/20 blur-[100px] rounded-full -z-10" />

      <div className="w-full max-w-5xl mx-auto px-6 pt-24 pb-24 text-center">

        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <h1 className="text-6xl font-bold mb-4">
            AccessLens
          </h1>

          <p className="text-slate-400 text-lg mb-10 max-w-2xl mx-auto">
            Automated WCAG accessibility auditing powered by multi-engine intelligence.
          </p>

          {/* Form */}
          <AuditForm
            url={url}
            setUrl={setUrl}
            onStartAudit={handleStartAudit}
            isLoading={startAudit.isPending}
            engines={engines}
          />

          <Link
            href="/dashboard"
            className="inline-block mt-6 text-blue-400 hover:text-blue-300"
          >
            Access Intelligence Dashboard
          </Link>
        </motion.div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20 w-full">

          <FeatureCard
            icon={<ShieldCheck />}
            title="Policy Enforcement"
            description="WCAG validation engine"
          />

          <FeatureCard
            icon={<Zap />}
            title="Instant Synthesis"
            description="Parallel engine execution"
          />

          <FeatureCard
            icon={<BarChart3 />}
            title="Visual Intelligence"
            description="AI + vision analysis"
          />

        </div>
      </div>
    </main>
  );
}