import { IssueSource } from '@/lib/types';

interface EngineBreakdownProps {
  data: Record<IssueSource, number>;
}

export function EngineBreakdown({ data }: EngineBreakdownProps) {
  const engineNames: Record<IssueSource, string> = {
    wcag_deterministic: 'WCAG Rules',
    structural: 'Structural',
    contrast: 'Contrast',
    ai_contextual: 'AI Analysis',
    heuristic: 'Heuristic',
  };

  const engineColors: Record<IssueSource, string> = {
    wcag_deterministic: 'bg-green-500',
    structural: 'bg-blue-500',
    contrast: 'bg-purple-500',
    ai_contextual: 'bg-orange-500',
    heuristic: 'bg-gray-500',
  };

  const total = Object.values(data).reduce((a, b) => a + b, 0);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Issues by Engine</h2>
      
      {total === 0 ? (
        <p className="text-gray-500 text-center py-8">No issues found</p>
      ) : (
        <div className="space-y-4">
          {(Object.entries(data) as [IssueSource, number][]).map(([engine, count]) => {
            if (count === 0) return null;
            const percentage = (count / total) * 100;
            
            return (
              <div key={engine}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium">{engineNames[engine] || engine}</span>
                  <span>{count} ({percentage.toFixed(1)}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`${engineColors[engine]} h-2 rounded-full`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
