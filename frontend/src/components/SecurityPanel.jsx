import { SeverityBadge } from './ImpactPanel.jsx'

export default function SecurityPanel({ codeReview }) {
  if (!codeReview) return <div className="text-slate-400 text-sm">No security data.</div>

  const { security_issues = [] } = codeReview

  if (security_issues.length === 0) {
    return (
      <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
        <span className="text-2xl">✓</span>
        <span className="font-medium">No security issues detected in this change.</span>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm font-medium">
        ⚠ {security_issues.length} security issue{security_issues.length !== 1 ? 's' : ''} detected — review before merging
      </div>

      {security_issues.map((f, i) => (
        <div key={i} className={`border rounded-lg p-4 ${
          f.severity === 'critical' ? 'border-red-400 bg-red-50' : 'border-orange-200 bg-orange-50'
        }`}>
          <div className="flex items-start gap-2 mb-2">
            <SeverityBadge severity={f.severity} />
            <span className="font-semibold text-slate-800">{f.title}</span>
          </div>
          <div className="text-xs text-slate-500 font-mono mb-2">
            {f.file}{f.function ? `::${f.function}` : ''}{f.line ? ` line ${f.line}` : ''}
          </div>
          <p className="text-sm text-slate-700 mb-2">{f.description}</p>
          {f.recommendation && (
            <div className="bg-white bg-opacity-70 border border-slate-200 rounded p-2 text-xs">
              <span className="font-semibold">Remediation: </span>
              {f.recommendation}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
