import { useState } from 'react'
import { api } from '../api/client.js'

export default function RepositoryInput({ onScanned, onUseSampleDiffs }) {
  const [repoPath, setRepoPath] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleScan = async () => {
    if (!repoPath.trim()) return
    setLoading(true)
    setError(null)
    try {
      const scan = await api.scanRepository(repoPath.trim(), description.trim())
      if (scan.error) {
        setError(scan.error)
      } else {
        onScanned(scan)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Primary card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shrink-0">1</div>
          <div>
            <h2 className="text-lg font-semibold text-slate-800">Analyze Your Repository</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Point ChangeGuard at a local project directory to scan its structure, detect frameworks, and read recent git changes.
            </p>
          </div>
        </div>

        {/* Path input */}
        <label className="block mb-3">
          <span className="text-sm font-medium text-slate-700">Repository path</span>
          <input
            type="text"
            className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-400 bg-slate-50"
            placeholder="/home/user/my-project  or  C:\projects\my-app"
            value={repoPath}
            onChange={e => setRepoPath(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !loading && handleScan()}
          />
        </label>

        {/* Optional description */}
        <label className="block mb-4">
          <span className="text-sm font-medium text-slate-700">
            Project description <span className="text-slate-400 font-normal">(optional)</span>
          </span>
          <textarea
            rows={2}
            className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-slate-50 resize-none"
            placeholder='e.g. "E-commerce backend — authenticated users place orders, admins manage products."'
            value={description}
            onChange={e => setDescription(e.target.value)}
          />
        </label>

        {error && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <button
          onClick={handleScan}
          disabled={loading || !repoPath.trim()}
          className="w-full py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Scanning repository…' : 'Scan Repository →'}
        </button>
      </div>

      {/* Divider + fallback */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px bg-slate-200" />
        <span className="text-xs text-slate-400">or</span>
        <div className="flex-1 h-px bg-slate-200" />
      </div>

      <button
        onClick={onUseSampleDiffs}
        className="w-full py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 hover:border-slate-400 transition-colors"
      >
        Use Sample Diffs / Paste Custom Diff (Demo)
      </button>
    </div>
  )
}
