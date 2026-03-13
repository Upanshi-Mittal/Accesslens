import { IssueSeverity } from '@/lib/types';

interface SeverityBadgeProps {
  severity: IssueSeverity;
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const classes = {
    critical: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
    serious: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    moderate: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    minor: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  };

  return (
    <span className={`px-2.5 py-1 text-[10px] font-black uppercase tracking-widest rounded-md border ${classes[severity]}`}>
      {severity}
    </span>
  );
}
