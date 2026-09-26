import { useState } from 'react'
import ReleaseBadge from './ReleaseBadge.jsx'
import ImpactPanel from './ImpactPanel.jsx'
import CodeReviewPanel from './CodeReviewPanel.jsx'
import SecurityPanel from './SecurityPanel.jsx'
import TestGapPanel from './TestGapPanel.jsx'
import TestGenPanel from './TestGenPanel.jsx'
import TestResultsPanel from './TestResultsPanel.jsx'

const TABS = [
  { key: 'verdict', label: 'Release Verdict' },
  { key: 'impact', label: 'Impact' },
  { key: 'code', label: 'Code Review' },
  { key: 'security', label: 'Security' },
  { key: 'gaps', label: 'Test Gaps' },
  { key: 'generated', label: 'Generated Tests' },
  { key: 'results', label: 'Test Results' },
]

export default function ReportDashboard({ report }) {
  const [tab, setTab] = useState('verdict')

  if (!report) return null

  const secCount = report.code_review?.security_issues?.length || 0
  const bugCount = report.code_review?.bugs?.length || 0
  const gapPct = Math.round((report.test_gap?.gap_score || 0) * 100)

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      {/* Tab bar */}
      <div className="flex overflow-x-auto border-b border-slate-200 bg-slate-50">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              tab === t.key
                ? 'border-blue-500 text-blue-700 bg-white'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {t.label}
            {t.key === 'security' && secCount > 0 && (
              <span className="ml-1.5 bg-red-500 text-white text-xs rounded-full px-1.5">{secCount}</span>
            )}
            {t.key === 'code' && bugCount > 0 && (
              <span className="ml-1.5 bg-orange-500 text-white text-xs rounded-full px-1.5">{bugCount}</span>
            )}
            {t.key === 'gaps' && gapPct > 0 && (
              <span className="ml-1.5 bg-amber-400 text-slate-800 text-xs rounded-full px-1.5">{gapPct}%</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-6">
        {tab === 'verdict' && (
          <div className="space-y-4">
            <ReleaseBadge
              verdict={report.release_verdict}
              reasons={report.verdict_reasons}
            />
            {/* Quick stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Stat label="Changed Files" value={report.impact?.changed_files?.length || 0} />
              <Stat label="Security Issues" value={secCount} warn={secCount > 0} />
              <Stat label="Bugs Found" value={bugCount} warn={bugCount > 0} />
              <Stat label="Test Gap" value={`${gapPct}%`} warn={gapPct >= 50} />
            </div>
            <div className="text-xs text-slate-400">
              Report ID: {report.id} · Generated: {new Date(report.created_at).toLocaleString()}
            </div>
          </div>
        )}
        {tab === 'impact' && <ImpactPanel impact={report.impact} />}
        {tab === 'code' && <CodeReviewPanel codeReview={report.code_review} />}
        {tab === 'security' && <SecurityPanel codeReview={report.code_review} />}
        {tab === 'gaps' && <TestGapPanel testGap={report.test_gap} />}
        {tab === 'generated' && <TestGenPanel testGen={report.test_gen} />}
        {tab === 'results' && <TestResultsPanel testRun={report.test_run} />}
      </div>
    </div>
  )
}

function Stat({ label, value, warn }) {
  return (
    <div className={`rounded-lg border p-3 text-center ${warn ? 'border-orange-200 bg-orange-50' : 'border-slate-200 bg-slate-50'}`}>
      <div className={`text-2xl font-bold ${warn ? 'text-orange-600' : 'text-slate-700'}`}>{value}</div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  )
}
