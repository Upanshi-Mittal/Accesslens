interface ScoreGaugeProps {
  score: number;
}

export function ScoreGauge({ score }: ScoreGaugeProps) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Accessibility Score</h2>
      <div className="flex flex-col items-center">
        <div className="relative w-32 h-32 mb-4">
          <svg className="w-full h-full" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="10"
            />
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke={score >= 90 ? '#10b981' : score >= 70 ? '#eab308' : score >= 50 ? '#f97316' : '#ef4444'}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={\\\}
              strokeDashoffset={\\\}
              transform="rotate(-90 50 50)"
            />
            <text
              x="50"
              y="50"
              textAnchor="middle"
              dy=".3em"
              className={\	ext-2xl font-bold \\}
            >
              {Math.round(score)}
            </text>
          </svg>
        </div>
        <div className={\	ext-xl font-bold \\}>
          {getScoreLabel(score)}
        </div>
      </div>
    </div>
  );
}
