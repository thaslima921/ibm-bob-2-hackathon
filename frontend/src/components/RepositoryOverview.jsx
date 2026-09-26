export default function RepositoryOverview({ scan, onSelectChange, onBack }) {
  const langBadgeColors = [
    'bg-blue-100 text-blue-700 border-blue-200',
    'bg-purple-100 text-purple-700 border-purple-200',
    'bg-green-100 text-green-700 border-green-200',
    'bg-amber-100 text-amber-700 border-amber-200',
    'bg-pink-100 text-pink-700 border-pink-200',
  ]

  return (
    <div className="space-y-4">
      {/* Header card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-green-600 flex items-center justify-center text-white font-bold text-sm shrink-0">2</div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800">Repository Overview</h2>
              <p className="text-xs text-slate-500 font-mono mt-0.5 truncate max-w-xs">{scan.repository_path}</p>
            </div>
          </div>
          <button
            onClick={onBack}
            className="text-xs text-slate-500 hover:text-slate-700 border border-slate-200 rounded-lg px-3 py-1.5 hover:bg-slate-50 transition-colors"
          >
            ← Back
          </button>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <StatCard label="Source Files" value={scan.source_file_count} />
          <StatCard label="Test Files" value={scan.test_file_count} />
          <StatCard label="Config Files" value={scan.config_file_count} />
        </div>

        {/* Languages */}
        {scan.detected_languages.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Languages</p>
            <div className="flex flex-wrap gap-1.5">
              {scan.detected_languages.map((lang, i) => (
                <span
                  key={lang}
                  className={`text-xs font-medium px-2 py-0.5 rounded border ${langBadgeColors[i % langBadgeColors.length]}`}
                >
                  {lang}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Frameworks */}
        {scan.framework_indicators.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Detected Frameworks</p>
            <div className="flex flex-wrap gap-1.5">
              {scan.framework_indicators.map(fw => (
                <span key={fw} className="text-xs font-medium px-2 py-0.5 rounded border bg-slate-100 text-slate-700 border-slate-200">
                  {fw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Dependency files */}
        {scan.dependency_files.length > 0 && (
          <div className="mb-3">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Dependency Files</p>
            <div className="flex flex-wrap gap-1.5">
              {scan.dependency_files.map(f => (
                <span key={f} className="text-xs font-mono px-2 py-0.5 rounded border bg-amber-50 text-amber-700 border-amber-200">
                  {f}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Optional description */}
        {scan.description && (
          <div className="mb-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Project Description</p>
            <p className="text-sm text-slate-700">{scan.description}</p>
          </div>
        )}

        {/* Git status */}
        <div className={`rounded-lg border px-4 py-3 ${scan.is_git_repo ? 'bg-green-50 border-green-200' : 'bg-slate-50 border-slate-200'}`}>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-bold ${scan.is_git_repo ? 'text-green-700' : 'text-slate-500'}`}>
              {scan.is_git_repo ? '⎇ Git repository' : 'Not a Git repository'}
            </span>
            {scan.current_branch && (
              <span className="text-xs text-green-600 font-mono bg-green-100 px-2 py-0.5 rounded">
                {scan.current_branch}
              </span>
            )}
          </div>
          {scan.latest_commit && (
            <p className="text-xs text-slate-600 mt-1">Latest: {scan.latest_commit}</p>
          )}
        </div>
      </div>

      {/* CTA */}
      <button
        onClick={onSelectChange}
        className="w-full py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
      >
        {scan.is_git_repo ? 'Select a Change to Analyze →' : 'Continue to Diff Selection →'}
      </button>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-center">
      <div className="text-2xl font-bold text-slate-700">{value}</div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  )
}
