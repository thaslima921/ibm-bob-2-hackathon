import { useState } from 'react'
import { api } from '../api/client.js'

// Simple client-side check — the backend does authoritative validation.
function looksLikeGitHubUrl(value) {
  return /^https:\/\/github\.com\/[^/]+\/[^/]/.test(value.trim())
}

export default function RepositoryInput({ onScanned, onUseSampleDiffs }) {
  const [repoUrl, setRepoUrl] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleScan = async () => {
    const url = repoUrl.trim()
    if (!url) return
    setLoading(true)
    setError(null)
    try {
      const scan = await api.scanRepository(url, description.trim())
      if (scan.error) {
        setError(scan.error)
      } else {
        onScanned(scan)
      }
    } catch (e) {
      // Surface a readable message for common failure modes
      const msg = e.message || 'Unknown error'
      if (msg.includes('502') || msg.includes('clone')) {
        setError(
          'Could not clone the repository. Check that the URL is correct and the repository is public.'
        )
      } else if (msg.includes('422')) {
        setError(
          'Invalid GitHub URL. Use the full HTTPS URL, e.g. https://github.com/owner/repo'
        )
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  const urlIsValid = looksLikeGitHubUrl(repoUrl)
  const canSubmit = !loading && urlIsValid

  return (
    <div className="space-y-4">
      {/* Primary card */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm shrink-0">1</div>
          <div>
            <h2 className="text-lg font-semibold text-slate-800">Analyze a GitHub Repository</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Enter a public GitHub repository URL. ChangeGuard will clone it, inspect its structure, and list recent commits for analysis.
            </p>
          </div>
        </div>

        {/* URL input */}
        <label className="block mb-3">
          <span className="text-sm font-medium text-slate-700">GitHub Repository URL</span>
          <input
            type="url"
            className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-400 bg-slate-50"
            placeholder="https://github.com/owner/repository"
            value={repoUrl}
            onChange={e => setRepoUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && canSubmit && handleScan()}
          />
          <p className="mt-1 text-xs text-slate-400">
            Public GitHub repositories only · HTTPS URLs · Example:{' '}
            <span className="font-mono">https://github.com/thaslima921/ibm-bob-2-hackathon</span>
          </p>
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

        {/* Inline URL format warning (before submit) */}
        {repoUrl && !urlIsValid && (
          <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm">
            URL must start with <span className="font-mono">https://github.com/</span> and include an owner and repository name.
          </div>
        )}

        {error && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        <button
          onClick={handleScan}
          disabled={!canSubmit}
          className="w-full py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin inline-block" />
              Cloning &amp; scanning repository…
            </span>
          ) : 'Scan Repository →'}
        </button>

        {loading && (
          <p className="mt-2 text-center text-xs text-slate-400">
            This may take up to 2 minutes for large repositories.
          </p>
        )}
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
