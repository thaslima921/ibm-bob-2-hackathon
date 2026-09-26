export default function ImpactPanel({ impact }) {
  if (!impact) return <div className="text-slate-400 text-sm">No impact data.</div>

  const { changed_files = [], changed_functions = [], ripple_risk_areas = [] } = impact

  return (
    <div className="space-y-6">
      {/* Changed files */}
      <section>
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">
          Changed Files ({changed_files.length})
        </h3>
        {changed_files.length === 0 ? (
          <p className="text-slate-400 text-sm">No files changed.</p>
        ) : (
          <div className="space-y-2">
            {changed_files.map((f, i) => (
              <div key={i} className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg px-4 py-2">
                <span className="font-mono text-sm text-slate-700">{f.path}</span>
                <div className="flex gap-3 text-xs">
                  <span className="text-green-600">+{f.added_lines}</span>
                  <span className="text-red-500">−{f.removed_lines}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Changed functions */}
      <section>
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">
          Changed Functions ({changed_functions.length})
        </h3>
        {changed_functions.length === 0 ? (
          <p className="text-slate-400 text-sm">No functions detected.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {changed_functions.map((fn, i) => (
              <span key={i} className="bg-blue-50 border border-blue-200 text-blue-700 text-xs font-mono px-2 py-1 rounded">
                {fn}
              </span>
            ))}
          </div>
        )}
      </section>

      {/* Ripple risks */}
      <section>
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">
          Ripple Risk Areas ({ripple_risk_areas.length})
        </h3>
        {ripple_risk_areas.length === 0 ? (
          <p className="text-slate-400 text-sm">No ripple risks detected.</p>
        ) : (
          <div className="space-y-2">
            {ripple_risk_areas.map((r, i) => (
              <div key={i} className={`border rounded-lg p-3 ${
                r.severity === 'critical' ? 'border-red-300 bg-red-50' :
                r.severity === 'high' ? 'border-orange-200 bg-orange-50' :
                'border-yellow-200 bg-yellow-50'
              }`}>
                <div className="flex items-center gap-2 mb-1">
                  <SeverityBadge severity={r.severity} />
                  <span className="font-medium text-sm text-slate-800">{r.area}</span>
                </div>
                <p className="text-xs text-slate-600">{r.reason}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function SeverityBadge({ severity }) {
  const colors = {
    critical: 'bg-red-600 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-yellow-400 text-slate-800',
    low: 'bg-slate-200 text-slate-700',
  }
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded ${colors[severity] || colors.low}`}>
      {severity?.toUpperCase()}
    </span>
  )
}

export { SeverityBadge }
