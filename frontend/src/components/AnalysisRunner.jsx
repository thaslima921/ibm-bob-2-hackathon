const STAGES = [
  { key: 'impact', label: 'Impact Analysis' },
  { key: 'code_review', label: 'Code & Bug Review' },
  { key: 'test_gap', label: 'Test Gap Analysis' },
  { key: 'test_gen', label: 'Test Generation' },
  { key: 'test_run', label: 'Test Execution' },
]

function StageIcon({ status }) {
  if (status === 'done') return <span className="text-green-500">✓</span>
  if (status === 'running') return <span className="text-blue-500 animate-pulse">⟳</span>
  if (status === 'error') return <span className="text-red-500">✗</span>
  return <span className="text-slate-300">○</span>
}

export default function AnalysisRunner({ job, polling, error }) {
  if (!job && !error) return null

  const subStatus = job?.subagent_status || {}

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-800">Analysis Progress</h2>
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${
          job?.status === 'complete' ? 'bg-green-100 text-green-700' :
          job?.status === 'error' ? 'bg-red-100 text-red-700' :
          'bg-blue-100 text-blue-700'
        }`}>
          {job?.status ?? 'starting'}
        </span>
      </div>

      <div className="space-y-2">
        {STAGES.map(s => (
          <div key={s.key} className="flex items-center gap-3">
            <div className="w-5 text-center text-lg">
              <StageIcon status={subStatus[s.key] ?? 'pending'} />
            </div>
            <div className={`text-sm ${
              subStatus[s.key] === 'running' ? 'text-blue-700 font-medium' :
              subStatus[s.key] === 'done' ? 'text-slate-600' :
              subStatus[s.key] === 'error' ? 'text-red-600' :
              'text-slate-400'
            }`}>
              {s.label}
            </div>
            {subStatus[s.key] === 'running' && (
              <div className="flex-1 h-1 bg-slate-100 rounded overflow-hidden">
                <div className="h-full bg-blue-400 animate-pulse w-2/3" />
              </div>
            )}
          </div>
        ))}
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm whitespace-pre-wrap font-mono">
          {error}
        </div>
      )}
    </div>
  )
}
