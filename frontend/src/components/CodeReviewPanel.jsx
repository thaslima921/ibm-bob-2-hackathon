import { SeverityBadge } from './ImpactPanel.jsx'

function FindingCard({ finding }) {
  return (
    <div className={`border rounded-lg p-4 ${
      finding.severity === 'critical' ? 'border-red-300 bg-red-50' :
      finding.severity === 'high' ? 'border-orange-200 bg-orange-50' :
      finding.severity === 'medium' ? 'border-yellow-200 bg-yellow-50' :
      'border-slate-200 bg-slate-50'
    }`}>
      <div className="flex items-start gap-2 mb-2">
        <SeverityBadge severity={finding.severity} />
        <span className="font-medium text-slate-800 text-sm">{finding.title}</span>
      </div>
      <div className="text-xs text-slate-500 font-mono mb-1">
        {finding.file}{finding.function ? `::${finding.function}` : ''}{finding.line ? ` line ${finding.line}` : ''}
      </div>
      <p className="text-sm text-slate-700 mb-2">{finding.description}</p>
      {finding.recommendation && (
        <div className="bg-white bg-opacity-60 border border-slate-200 rounded p-2 text-xs text-slate-600">
          <span className="font-semibold text-slate-700">Fix: </span>
          {finding.recommendation}
        </div>
      )}
    </div>
  )
}

export default function CodeReviewPanel({ codeReview }) {
  if (!codeReview) return <div className="text-slate-400 text-sm">No review data.</div>

  const { bugs = [], quality_issues = [], severity_counts = {} } = codeReview

  const allFindings = [...bugs, ...quality_issues]

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="flex gap-3 flex-wrap">
        {Object.entries(severity_counts)
          .filter(([k]) => ['critical','high','medium','low'].includes(k))
          .sort(([a], [b]) => ['critical','high','medium','low'].indexOf(a) - ['critical','high','medium','low'].indexOf(b))
          .map(([sev, count]) => (
            <div key={sev} className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg px-3 py-2">
              <SeverityBadge severity={sev} />
              <span className="text-slate-700 text-sm font-semibold">{count}</span>
            </div>
          ))}
      </div>

      {/* Bugs */}
      {bugs.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">
            Bugs ({bugs.length})
          </h3>
          <div className="space-y-2">
            {bugs.map((f, i) => <FindingCard key={i} finding={f} />)}
          </div>
        </section>
      )}

      {/* Quality */}
      {quality_issues.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">
            Quality Issues ({quality_issues.length})
          </h3>
          <div className="space-y-2">
            {quality_issues.map((f, i) => <FindingCard key={i} finding={f} />)}
          </div>
        </section>
      )}

      {allFindings.length === 0 && (
        <p className="text-slate-400 text-sm">No code issues found.</p>
      )}
    </div>
  )
}
