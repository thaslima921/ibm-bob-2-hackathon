import { useState } from 'react'

export default function TestGenPanel({ testGen }) {
  const [openIdx, setOpenIdx] = useState(0)

  if (!testGen || !testGen.generated_tests?.length) {
    return <div className="text-slate-400 text-sm">No tests generated.</div>
  }

  const tests = testGen.generated_tests

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">
        {tests.length} targeted test{tests.length !== 1 ? 's' : ''} generated for detected gaps.
      </p>
      {tests.map((t, i) => (
        <div key={i} className="border border-slate-200 rounded-lg overflow-hidden">
          <button
            onClick={() => setOpenIdx(openIdx === i ? -1 : i)}
            className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 hover:bg-slate-100 text-left"
          >
            <div>
              <span className="font-mono text-sm text-blue-700">{t.function}</span>
              <p className="text-xs text-slate-500 mt-0.5">{t.rationale}</p>
            </div>
            <span className="text-slate-400 text-lg">{openIdx === i ? '▲' : '▼'}</span>
          </button>
          {openIdx === i && (
            <pre className="bg-slate-900 text-slate-100 text-xs p-4 overflow-x-auto whitespace-pre">
              {t.test_code}
            </pre>
          )}
        </div>
      ))}
    </div>
  )
}
