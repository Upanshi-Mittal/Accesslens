'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { 
  AlertCircle, 
  CheckCircle2, 
  BarChart3,
  Search,
  History,
  Info,
  Layers,
  Sparkles,
  Globe,
  Target,
  Maximize2,
  Table
} from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScoreCard } from '@/components/audit/ScoreCard';
import { IssueList } from '@/components/audit/IssueList';
import { SeverityChart } from '@/components/charts/SeverityChart';
import { CoverageComparator } from '@/components/charts/CoverageComparator';
import { HeatmapOverlay } from '@/components/audit/HeatmapOverlay';
import { ConfidenceGauge } from '@/components/charts/ConfidenceGauge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function AuditResultsPage() {
  const params = useParams();
  const id = params.id as string;
  const [activeTab, setActiveTab] = useState<'issues' | 'heatmap' | 'analytics'>('issues');

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['audit', id],
    queryFn: () => api.getAuditResults(id),
    refetchInterval: (query) => {
       // Stop polling once report is available and has issues or is complete
       return query.state.data ? false : 3000;
    }
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-brand-500/5 blur-[100px] rounded-full"></div>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="text-brand-500 mb-8"
        >
          <LoadingSpinner />
        </motion.div>
        <h1 className="text-2xl font-black text-white tracking-widest uppercase mb-2">Analyzing Architecture</h1>
        <p className="text-slate-400 font-bold text-xs uppercase tracking-[0.3em]">Synthesizing Engine Intelligence...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center">
        <div className="w-20 h-20 bg-rose-500/10 rounded-full flex items-center justify-center text-rose-500 mb-8">
          <AlertCircle size={40} />
        </div>
        <h1 className="text-3xl font-black text-white mb-4 italic uppercase tracking-tighter">Signal Interrupted</h1>
        <p className="text-slate-400 max-w-md mx-auto mb-8 font-medium">
          The intelligence report at identifier <span className="text-rose-400 font-mono">[{id}]</span> could not be retrieved from the collective base.
        </p>
        <button 
          onClick={() => window.location.reload()}
          className="btn-vibrant px-8 py-3"
        >
          Re-establish Connection
        </button>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 pb-24 relative overflow-hidden">
      {/* HUD Header */}
      <header className="sticky top-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/50 shadow-2xl">
        <div className="container-custom py-4 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-brand-600 flex items-center justify-center shadow-[0_0_20px_rgba(var(--brand-500),0.4)]">
              <Globe className="text-white" size={24} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-tight truncate max-w-[300px]">{report.request.url}</h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-black bg-brand-500/10 text-brand-400 border border-brand-500/20 uppercase tracking-widest">Live</span>
              </div>
              <p className="text-[10px] font-black uppercase text-slate-500 tracking-widest">
                Scanned {new Date(report.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
          
          <div className="flex bg-slate-900/50 p-1.5 rounded-2xl border border-slate-800">
            <TabButton 
              active={activeTab === 'issues'} 
              onClick={() => setActiveTab('issues')}
              icon={<Table size={16} />}
              label="Issue Matrix"
            />
            <TabButton 
              active={activeTab === 'heatmap'} 
              onClick={() => setActiveTab('heatmap')}
              icon={<Target size={16} />}
              label="Spatial Map"
            />
            <TabButton 
              active={activeTab === 'analytics'} 
              onClick={() => setActiveTab('analytics')}
              icon={<History size={16} />}
              label="Intelligence"
            />
          </div>
        </div>
      </header>

      <div className="container-custom mt-12">
        <AnimatePresence mode="wait">
          {activeTab === 'issues' && (
            <motion.div
              key="issues"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-12"
            >
              {/* Metric Pulse */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <ScoreCard 
                  title="Health Index" 
                  value={`${report.summary.score}%`} 
                  icon={<ShieldCheckIcon className="text-brand-500" />} 
                  trend="+4.2%" 
                  color="from-brand-500/20 to-indigo-500/20" 
                />
                <ScoreCard 
                  title="Barriers" 
                  value={report.summary.total_issues} 
                  icon={<AlertCircle className="text-rose-500" />} 
                  color="from-rose-500/20 to-orange-500/20" 
                />
                <ScoreCard 
                  title="Intelligence" 
                  value={`${report.summary.confidence_avg}%`} 
                  icon={<Sparkles className="text-amber-500" />} 
                  color="from-amber-500/20 to-yellow-500/20" 
                />
                <ScoreCard 
                  title="Dimensions" 
                  value={report.summary.by_wcag_level.AA || 0} 
                  icon={<Layers className="text-indigo-500" />} 
                  subtitle="AA Compliant" 
                  color="from-indigo-500/20 to-violet-500/20" 
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                <div className="lg:col-span-2 space-y-8">
                  <div className="flex items-center justify-between">
                    <h2 className="text-sm font-black uppercase tracking-[0.3em] text-slate-500">Barrier Manifest</h2>
                    <div className="flex gap-2">
                       <span className="px-3 py-1 bg-slate-900 rounded-full border border-slate-800 text-[10px] font-black uppercase text-slate-400">Filter: All</span>
                    </div>
                  </div>
                  <IssueList issues={report.issues} />
                </div>
                <div className="space-y-8">
                  <SeverityChart data={report.summary.by_severity} />
                  <ConfidenceGauge confidence={report.summary.confidence_avg} />
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'heatmap' && (
            <motion.div
              key="heatmap"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
            >
              <div className="mb-8">
                <h2 className="text-3xl font-black text-white italic tracking-tighter uppercase mb-2">Spatial Distribution</h2>
                <p className="text-slate-400">Visual mapping of accessibility barriers across the viewport geometry.</p>
              </div>
              <HeatmapOverlay 
                issues={report.issues} 
                screenshot={report.metadata.full_screenshot} 
                viewportWidth={report.request.viewport?.width || 1280}
              />
            </motion.div>
          )}

          {activeTab === 'analytics' && (
            <motion.div
              key="analytics"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-12"
            >
              <CoverageComparator summary={report.summary} />
              
              <div className="glass-card p-10 border-slate-800">
                <h2 className="text-sm font-black uppercase tracking-widest text-slate-500 mb-8">Audit Telemetry</h2>
                <dl className="space-y-6">
                  <TelemetryItem label="Scan Duration" value={`${report.metadata.duration_seconds}s`} />
                  <TelemetryItem label="Unique Elements" value={report.accessibility_tree?.node_count || report.metadata.total_elements || 'Unknown'} />
                  <TelemetryItem label="Active Engines" value={report.metadata.engines_run?.join(', ')} />
                  <TelemetryItem label="Report Entropy" value={id.substring(0, 8)} />
                </dl>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}

function TabButton({ active, onClick, icon, label }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string }) {
  return (
    <button
      onClick={onClick}
      className={`
        relative px-6 py-2 rounded-xl flex items-center gap-3 transition-all duration-300
        ${active ? 'text-white' : 'text-slate-500 hover:text-slate-300'}
      `}
    >
      {active && (
        <motion.div 
          layoutId="activeTab"
          className="absolute inset-0 bg-brand-500/10 border border-brand-500/20 rounded-xl"
        />
      )}
      <span className="relative z-10">{icon}</span>
      <span className="relative z-10 text-[10px] font-black uppercase tracking-widest">{label}</span>
    </button>
  );
}

function TelemetryItem({ label, value }: { label: string, value: any }) {
  return (
    <div className="flex justify-between items-baseline py-4 border-b border-slate-900 last:border-0">
      <dt className="text-[10px] font-black uppercase tracking-widest text-slate-600">{label}</dt>
      <dd className="text-sm font-bold text-white">{value}</dd>
    </div>
  );
}

function ShieldCheckIcon(props: any) {
  return <CheckCircle2 {...props} />;
}
