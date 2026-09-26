import { useState } from 'react'
import { api } from './api/client.js'
import { useAnalysis } from './hooks/useAnalysis.js'
import RepositoryInput from './components/RepositoryInput.jsx'
import RepositoryOverview from './components/RepositoryOverview.jsx'
import SelectChange from './components/SelectChange.jsx'
import AnalysisRunner from './components/AnalysisRunner.jsx'
import ReportDashboard from './components/ReportDashboard.jsx'

// App-level flow steps
// 'repo-input'    → user enters repo path
// 'repo-overview' → scan results shown
// 'select-change' → pick commit or diff
// 'analyzing'     → pipeline running / done
const STEP_REPO_INPUT = 'repo-input'
const STEP_OVERVIEW   = 'repo-overview'
const STEP_CHANGE     = 'select-change'
const STEP_ANALYZING  = 'analyzing'

export default function App() {
  const [step, setStep] = useState(STEP_REPO_INPUT)
  const [scan, setScan] = useState(null)           // RepositoryScan from backend
  const [usingSampleFlow, setUsingSampleFlow] = useState(false)

  const [jobId, setJobId] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)

  const { job, report, polling, error: pollError } = useAnalysis(jobId)

  // ----------------------------------------------------------------
  // Handlers
  // ----------------------------------------------------------------

  const handleScanned = (scannedRepo) => {
    setScan(scannedRepo)
    setStep(STEP_OVERVIEW)
  }

  const handleUseSampleDiffs = () => {
    setUsingSampleFlow(true)
    setScan(null)
    setStep(STEP_CHANGE)
  }

  const handleSelectChange = () => {
    setStep(STEP_CHANGE)
  }

  const handleBackToInput = () => {
    setScan(null)
    setUsingSampleFlow(false)
    setStep(STEP_REPO_INPUT)
  }

  const handleBackToOverview = () => {
    if (scan && !usingSampleFlow) {
      setStep(STEP_OVERVIEW)
    } else {
      handleBackToInput()
    }
  }

  const handleSubmitAnalysis = async (diffId, diffText, label, repositoryId, projectDescription) => {
    setSubmitting(true)
    setSubmitError(null)
    setJobId(null)
    try {
      const j = await api.startAnalysis(
        diffId,
        diffText,
        label,
        repositoryId || null,
        projectDescription || '',
      )
      setJobId(j.id)
      setStep(STEP_ANALYZING)
    } catch (e) {
      setSubmitError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleAnalyzeAgain = () => {
    setJobId(null)
    setSubmitError(null)
    // Return to change selection (or repo input if no scan)
    if (scan && !usingSampleFlow) {
      setStep(STEP_CHANGE)
    } else if (usingSampleFlow) {
      setStep(STEP_CHANGE)
    } else {
      setStep(STEP_REPO_INPUT)
    }
  }

  const loading = submitting || polling

  // ----------------------------------------------------------------
  // Render
  // ----------------------------------------------------------------

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center gap-3">
        <div
          className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-sm cursor-pointer"
          onClick={handleBackToInput}
          title="Go to start"
        >
          CG
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">ChangeGuard</h1>
          <p className="text-xs text-slate-500">Code Change Risk &amp; Release Readiness Analysis</p>
        </div>
        {/* Step indicator */}
        <div className="ml-auto hidden sm:flex items-center gap-1 text-xs text-slate-400">
          <StepDot n={1} active={step === STEP_REPO_INPUT} done={step !== STEP_REPO_INPUT} label="Repository" />
          <div className="w-4 h-px bg-slate-200" />
          <StepDot n={2} active={step === STEP_OVERVIEW} done={[STEP_CHANGE, STEP_ANALYZING].includes(step) && !usingSampleFlow} label="Overview" />
          <div className="w-4 h-px bg-slate-200" />
          <StepDot n={3} active={step === STEP_CHANGE} done={step === STEP_ANALYZING} label="Change" />
          <div className="w-4 h-px bg-slate-200" />
          <StepDot n={4} active={step === STEP_ANALYZING} done={false} label="Analysis" />
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {submitError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            <strong>Error submitting analysis:</strong> {submitError}
          </div>
        )}

        {/* Step 1: Repository Input */}
        {step === STEP_REPO_INPUT && (
          <RepositoryInput
            onScanned={handleScanned}
            onUseSampleDiffs={handleUseSampleDiffs}
          />
        )}

        {/* Step 2: Repository Overview */}
        {step === STEP_OVERVIEW && scan && (
          <RepositoryOverview
            scan={scan}
            onSelectChange={handleSelectChange}
            onBack={handleBackToInput}
          />
        )}

        {/* Step 3: Select Change */}
        {step === STEP_CHANGE && (
          <SelectChange
            scan={usingSampleFlow ? null : scan}
            onSubmit={handleSubmitAnalysis}
            loading={loading}
            onBack={scan && !usingSampleFlow ? handleBackToOverview : handleBackToInput}
          />
        )}

        {/* Step 4: Analysis running + results */}
        {step === STEP_ANALYZING && (
          <>
            {(jobId || submitting) && (
              <AnalysisRunner job={job} polling={polling} error={pollError} />
            )}
            {report && (
              <>
                <ReportDashboard report={report} />
                <div className="text-center">
                  <button
                    onClick={handleAnalyzeAgain}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    ← Analyze another change
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </main>

      <footer className="text-center text-xs text-slate-400 py-6 border-t border-slate-200 mt-8">
        ChangeGuard MVP · Built with IBM Bob
      </footer>
    </div>
  )
}

function StepDot({ n, active, done, label }) {
  return (
    <div className="flex items-center gap-1">
      <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
        done ? 'bg-green-500 text-white' :
        active ? 'bg-blue-600 text-white' :
        'bg-slate-200 text-slate-500'
      }`}>
        {done ? '✓' : n}
      </div>
      <span className={`text-xs ${active ? 'text-blue-600 font-medium' : 'text-slate-400'}`}>{label}</span>
    </div>
  )
}
