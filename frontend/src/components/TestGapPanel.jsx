export default function TestGapPanel({ testGap }) {
  if (!testGap) return <div className="text-slate-400 text-sm">No test gap data.</div>

  const {
    covered_functions = [],
    uncovered_functions = [],
    missing_edge_cases = [],
    gap_score = 0,
  } = testGap

  const pct = Math.round(gap_score * 100)
  const barColor = gap_score >= 0.7 ? 'bg-red-500' : gap_score >= 0.4 ? 'bg-amber-400' : 'bg-green-500'

  return (
    <div className="space-y-6">
      {/* Gap score */}
      <div className="bg-white border border-slate-200 rounded-lg p-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-semibold text-slate-700">Coverage Gap Score</span>
          <span className={`text-lg font-bold ${gap_score >= 0.5 ? 'text-red-600' : 'text-green-600'}`}>
            {pct}% uncovered
          </span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-3">
          <div className={`${barColor} h-3 rounded-full transition-all`} style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-slate-500 mt-1">
          {covered_functions.length} covered · {uncovered_functions.length} uncovered
        </p>
      </div>

      {/* Uncovered functions */}
      {uncovered_functions.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">
            Uncovered Functions ({uncovered_functions.length})
          </h3>
          <div className="space-y-1">
            {uncovered_functions.map((fn, i) => (
              <div key={i} className="flex items-center gap-2 px-3 py-1.5 bg-red-50 border border-red-200 rounded text-sm">
                <span className="text-red-500">✗</span>
                <span className="font-mono text-red-700">{fn}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Covered functions */}
      {covered_functions.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">
            Covered Functions ({covered_functions.length})
          </h3>
          <div className="space-y-1">
            {covered_functions.map((fn, i) => (
              <div key={i} className="flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded text-sm">
                <span className="text-green-500">✓</span>
                <span className="font-mono text-green-700">{fn}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Missing edge cases */}
      {missing_edge_cases.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">
            Missing Edge Cases ({missing_edge_cases.length})
          </h3>
          <ul className="space-y-1">
            {missing_edge_cases.map((ec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                <span className="text-amber-500 mt-0.5 shrink-0">⚠</span>
                {ec}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
