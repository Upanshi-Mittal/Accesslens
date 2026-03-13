'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  Search, 
  History, 
  ArrowRight, 
  ShieldAlert, 
  Clock, 
  ExternalLink,
  ChevronRight,
  Database
} from 'lucide-react';
import { AuditReport } from '@/lib/types';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function DashboardPage() {
  const { data: reports, isLoading } = useQuery<AuditReport[]>({
    queryKey: ['audits'],
    queryFn: () => api.listAudits(20, 0),
  });

  const stats = {
    totalAudits: reports?.length || 0,
    avgScore: reports?.length 
      ? Math.round(reports.reduce((acc, r) => acc + r.summary.score, 0) / reports.length) 
      : 0,
    totalIssues: reports?.reduce((acc, r) => acc + r.summary.total_issues, 0) || 0,
  };

  return (
    <main className="min-h-screen bg-slate-950 pt-32 pb-24 relative overflow-hidden">
      {/* Decorative Background */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px] -z-10"></div>
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-brand-600/5 rounded-full blur-[100px] -z-10"></div>

      <div className="container-custom">
        <div className="mb-12">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-3 text-brand-400 mb-4"
          >
            <Database size={20} />
            <span className="text-sm font-black uppercase tracking-widest">Intelligence Center</span>
          </motion.div>
          <motion.h1 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-6xl font-black text-white tracking-tight"
          >
            Audit Dashboard
          </motion.h1>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          <StatCard 
            label="Total Audits" 
            value={stats.totalAudits} 
            icon={<History className="text-indigo-400" />} 
            delay={0.1}
          />
          <StatCard 
            label="Average Health" 
            value={`${stats.avgScore}%`} 
            icon={<ShieldAlert className="text-emerald-400" />} 
            delay={0.2}
          />
          <StatCard 
            label="Identified Barriers" 
            value={stats.totalIssues} 
            icon={<BarChart3 className="text-rose-400" />} 
            delay={0.3}
          />
        </div>

        {/* Audit List */}
        <div className="glass-card border-slate-800 overflow-hidden">
          <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/40">
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-400">Recent Reports</h2>
            <div className="flex items-center gap-2 text-xs font-bold text-slate-500">
              <Clock size={14} />
              <span>Auto-refreshing intelligence</span>
            </div>
          </div>

          {isLoading ? (
            <div className="py-20 flex justify-center">
              <LoadingSpinner />
            </div>
          ) : reports?.length === 0 ? (
            <div className="py-20 text-center">
              <Search size={48} className="mx-auto text-slate-800 mb-4" />
              <p className="text-slate-500 font-medium">No audit reports found in the intelligence base.</p>
              <Link href="/" className="text-brand-400 hover:text-brand-300 font-bold mt-4 inline-block">
                Start your first audit →
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-900">
              {reports?.map((report, index) => (
                <motion.div
                  key={report.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Link 
                    href={`/audit/${report.id}`}
                    className="flex flex-col md:flex-row md:items-center justify-between p-6 hover:bg-white/5 transition-colors group"
                  >
                    <div className="flex-1 min-w-0 mr-8">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="text-white font-bold truncate max-w-md">{report.request.url}</span>
                        <ExternalLink size={12} className="text-slate-600 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <div className="flex items-center gap-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                        <span>{formatDistanceToNow(new Date(report.timestamp), { addSuffix: true })}</span>
                        <span className="w-1 h-1 rounded-full bg-slate-800"></span>
                        <span className={`${report.summary.total_issues > 0 ? 'text-rose-500' : 'text-emerald-500'}`}>
                          {report.summary.total_issues} Issues
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-8 mt-4 md:mt-0">
                      <div className="text-right">
                        <div className="text-2xl font-black text-white">{report.summary.score}%</div>
                        <div className="text-[10px] font-black uppercase tracking-widest text-slate-600">Health Score</div>
                      </div>
                      <div className="w-10 h-10 rounded-full bg-slate-900 flex items-center justify-center text-slate-400 group-hover:bg-brand-500 group-hover:text-white transition-all">
                        <ChevronRight size={20} />
                      </div>
                    </div>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function StatCard({ label, value, icon, delay }: { label: string, value: string | number, icon: React.ReactNode, delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="glass-card p-8 border-slate-800 relative group overflow-hidden"
    >
      <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-100 transition-opacity transform group-hover:scale-110 duration-500">
        {icon}
      </div>
      <div className="text-sm font-black uppercase tracking-widest text-slate-500 mb-2">{label}</div>
      <div className="text-4xl font-black text-white">{value}</div>
      <div className="mt-4 w-full bg-slate-900 h-1 rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: '100%' }}
          transition={{ duration: 1, delay: delay + 0.5 }}
          className="h-full bg-brand-500/30"
        />
      </div>
    </motion.div>
  );
}
