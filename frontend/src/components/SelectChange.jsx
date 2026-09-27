import { useState, useEffect } from 'react'
import { api } from '../api/client.js'
import { SAMPLE_DIFFS } from '../data/sampleDiffs.js'

export default function SelectChange({ scan, onSubmit, loading, onBack }) {
  const [commits, setCommits] = useState(null)        // null = loading, [] = none
  const [commitsError, setCommitsError] = useState(null)
  const [selectedSha, setSelectedSha] = useState(null)

  // Fallback diff selector state (when git is unavailable)
  const [fallbackMode, setFallbackMode] = useState('sample') // 'sample' | 'custom'
  const [selectedSample, setSelectedSample] = useState(SAMPLE_DIFFS[0].id)
  const [customDiff, setCustomDiff] = useState('')

  useEffect(() => {
    if (!scan?.is_git_repo) {
      setCommits([])
      return
    }
    api.getRepositoryChanges(scan.id)
      .then(data => {
        setCommits(data)
        if (data.length > 0) setSelectedSha(data[0].sha)
      })
      .catch(e => {
        setCommitsError(e.message)
        setCommits([])
      })
  }, [scan?.id])

  const handleSubmitGit = async () => {
    if (!selectedSha) return
    const commit = commits.find(c => c.sha === selectedSha)
    if (!commit) return

    // Fetch the diff for this commit via git show
    try {
      // We ask the backend to diff via an inline endpoint — instead, we
      // generate the diff client-side label and pass it through the existing
      // /analysis endpoint with the commit SHA as diff_id.
      // The diff text is fetched from the backend /repository/{id}/diff/{sha}
      const { diff_text } = await api.getRepositoryDiff(
  scan.id,
  selectedSha
)
      onSubmit(
        `commit_${commit.short_sha}`,
        diff_text,
        commit.message,
        scan.id,
        scan.description,
      )
    } catch (e) {
      setCommitsError(e.message)
    }
  }

  const handleSubmitFallback = () => {
    if (fallbackMode === 'custom') {
      if (!customDiff.trim()) return
      onSubmit('custom_diff', customDiff.trim(), 'Custom diff', scan?.id || null, scan?.description || '')
    } else {
      const diff = SAMPLE_DIFFS.find(d => d.id === selectedSample)
      onSubmit(diff.id, diff.patch, diff.label, scan?.id || null, scan?.description || '')
    }
  }

  const showGitSection = scan?.is_git_repo && commits !== null

  return (
    <div className="space-y-4">
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-purple-600 flex items-center justify-center text-white font-bold text-sm shrink-0">3</div>
            <div>
              <h2 className="text-lg font-semibold text-slate-800">Select a Change</h2>
              {scan?.project_name && (
                <p className="text-xs text-slate-500 mt-0.5">{scan.project_name}</p>
              )}
            </div>
          </div>
          {onBack && (
            <button
              onClick={onBack}
              className="text-xs text-slate-500 hover:text-slate-700 border border-slate-200 rounded-lg px-3 py-1.5 hover:bg-slate-50 transition-colors"
            >
              ← Back
            </button>
          )}
        </div>

        {/* Git commits section */}
        {showGitSection && (
          <>
            {commits.length > 0 ? (
              <>
                <p className="text-xs text-slate-500 mb-3">
                  Recent commits on <span className="font-mono font-medium text-slate-700">{scan.current_branch}</span>
                </p>
                <div className="space-y-2 mb-4">
                  {commits.map(commit => (
                    <label
                      key={commit.sha}
                      className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedSha === commit.sha
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="commit"
                        value={commit.sha}
                        checked={selectedSha === commit.sha}
                        onChange={() => setSelectedSha(commit.sha)}
                        className="mt-0.5 shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                            {commit.short_sha}
                          </span>
                          <span className="text-sm font-medium text-slate-800 truncate">{commit.message}</span>
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                          <span>{commit.author}</span>
                          {commit.date && <span>{commit.date.slice(0, 10)}</span>}
                          {commit.files_changed > 0 && (
                            <span>{commit.files_changed} file{commit.files_changed !== 1 ? 's' : ''} changed</span>
                          )}
                          {commit.insertions > 0 && (
                            <span className="text-green-600">+{commit.insertions}</span>
                          )}
                          {commit.deletions > 0 && (
                            <span className="text-red-500">−{commit.deletions}</span>
                          )}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>

                {commitsError && (
                  <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {commitsError}
                  </div>
                )}

                <button
                  onClick={handleSubmitGit}
                  disabled={loading || !selectedSha}
                  className="w-full py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Analyzing…' : 'Run ChangeGuard on Selected Commit →'}
                </button>

                <div className="mt-4 flex items-center gap-3">
                  <div className="flex-1 h-px bg-slate-200" />
                  <span className="text-xs text-slate-400">or use a diff directly</span>
                  <div className="flex-1 h-px bg-slate-200" />
                </div>
              </>
            ) : (
              <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm">
                {commitsError
                  ? `Could not load git history: ${commitsError}`
                  : 'No commits found in this repository.'}
                {' '}Using diff input below.
              </div>
            )}
          </>
        )}

        {/* Fallback: sample / custom diff */}
        <div className={showGitSection && commits?.length > 0 ? 'mt-2' : ''}>
          {/* Toggle */}
          <div className="flex gap-2 mb-3">
            <button
              onClick={() => setFallbackMode('sample')}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                fallbackMode === 'sample'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Demo / Sample Diffs
            </button>
            <button
              onClick={() => setFallbackMode('custom')}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                fallbackMode === 'custom'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Paste Custom Diff
            </button>
          </div>

          {fallbackMode === 'sample' ? (
            <div className="space-y-2">
              {SAMPLE_DIFFS.map(diff => (
                <label
                  key={diff.id}
                  className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedSample === diff.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="sample"
                    value={diff.id}
                    checked={selectedSample === diff.id}
                    onChange={() => setSelectedSample(diff.id)}
                    className="mt-0.5 shrink-0"
                  />
                  <div>
                    <div className="font-medium text-slate-800 text-sm">{diff.label}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{diff.description}</div>
                  </div>
                </label>
              ))}
            </div>
          ) : (
            <textarea
              className="w-full h-40 font-mono text-xs border border-slate-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-slate-50"
              placeholder="Paste a unified diff here…"
              value={customDiff}
              onChange={e => setCustomDiff(e.target.value)}
            />
          )}

          <button
            onClick={handleSubmitFallback}
            disabled={loading || (fallbackMode === 'custom' && !customDiff.trim())}
            className="mt-3 w-full py-2.5 bg-slate-700 text-white font-semibold rounded-lg hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Analyzing…' : 'Analyze with Sample/Custom Diff →'}
          </button>
        </div>
      </div>
    </div>
  )
}
