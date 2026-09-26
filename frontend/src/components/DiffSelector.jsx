import { useState } from 'react'
import { SAMPLE_DIFFS } from '../data/sampleDiffs.js'

export default function DiffSelector({ onSubmit, loading }) {
  const [selected, setSelected] = useState(SAMPLE_DIFFS[0].id)
  const [custom, setCustom] = useState('')
  const [useCustom, setUseCustom] = useState(false)

  const handleSubmit = () => {
    if (useCustom) {
      if (!custom.trim()) return
      onSubmit('custom_diff', custom.trim(), 'Custom diff')
    } else {
      const diff = SAMPLE_DIFFS.find(d => d.id === selected)
      onSubmit(diff.id, diff.patch, diff.label)
    }
  }

  const activeDiff = SAMPLE_DIFFS.find(d => d.id === selected)

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Select Code Change</h2>

      {/* Toggle */}
      <div className="flex gap-4 mb-4">
        <button
          onClick={() => setUseCustom(false)}
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
            !useCustom ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          Sample Diffs
        </button>
        <button
          onClick={() => setUseCustom(true)}
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
            useCustom ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          Paste Custom Diff
        </button>
      </div>

      {!useCustom ? (
        <div className="space-y-3">
          {SAMPLE_DIFFS.map(diff => (
            <label
              key={diff.id}
              className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                selected === diff.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <input
                type="radio"
                name="diff"
                value={diff.id}
                checked={selected === diff.id}
                onChange={() => setSelected(diff.id)}
                className="mt-0.5"
              />
              <div>
                <div className="font-medium text-slate-800 text-sm">{diff.label}</div>
                <div className="text-xs text-slate-500 mt-0.5">{diff.description}</div>
              </div>
            </label>
          ))}

          {/* Preview */}
          {activeDiff && (
            <details className="mt-2">
              <summary className="text-xs text-blue-600 cursor-pointer hover:underline">
                Preview diff
              </summary>
              <pre className="mt-2 bg-slate-900 text-slate-100 text-xs rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
                {activeDiff.patch.slice(0, 800)}{activeDiff.patch.length > 800 ? '\n...' : ''}
              </pre>
            </details>
          )}
        </div>
      ) : (
        <textarea
          className="w-full h-48 font-mono text-xs border border-slate-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-slate-50"
          placeholder="Paste a unified diff here..."
          value={custom}
          onChange={e => setCustom(e.target.value)}
        />
      )}

      <button
        onClick={handleSubmit}
        disabled={loading || (useCustom && !custom.trim())}
        className="mt-4 w-full py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Analyzing…' : 'Analyze Change →'}
      </button>
    </div>
  )
}
