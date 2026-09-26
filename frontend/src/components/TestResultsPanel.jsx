export default function TestResultsPanel({ testRun }) {
  if (!testRun) return <div className="text-slate-400 text-sm">No test results.</div>

  const { passed = 0, failed = 0, errors = 0, output = '' } = testRun
  const total = passed + failed + errors

  return (
    <div className="space-y-4">
      {/* Summary counts */}
      <div className="flex gap-4">
        <div className="flex-1 bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-green-600">{passed}</div>
          <div className="text-xs text-green-600 font-medium mt-1">PASSED</div>
        </div>
        <div className="flex-1 bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-red-600">{failed}</div>
          <div className="text-xs text-red-600 font-medium mt-1">FAILED</div>
        </div>
        <div className="flex-1 bg-amber-50 border border-amber-200 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-amber-600">{errors}</div>
          <div className="text-xs text-amber-600 font-medium mt-1">ERRORS</div>
        </div>
      </div>

      {total === 0 && (
        <p className="text-slate-400 text-sm text-center">No tests were executed.</p>
      )}

      {/* Raw output */}
      {output && (
        <details>
          <summary className="text-xs text-blue-600 cursor-pointer hover:underline mb-2">
            View pytest output
          </summary>
          <pre className="bg-slate-900 text-slate-100 text-xs p-4 rounded-lg overflow-x-auto whitespace-pre-wrap max-h-96">
            {output}
          </pre>
        </details>
      )}
    </div>
  )
}
