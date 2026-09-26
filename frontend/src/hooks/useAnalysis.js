import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client.js'

/**
 * Polls GET /analysis/{jobId} every 2 seconds until status is complete or error.
 * Returns { job, report, polling, error }.
 */
export function useAnalysis(jobId) {
  const [job, setJob] = useState(null)
  const [report, setReport] = useState(null)
  const [polling, setPolling] = useState(false)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (!jobId) return
    setPolling(true)
    setError(null)
    setReport(null)

    const tick = async () => {
      try {
        const j = await api.getAnalysis(jobId)
        setJob(j)
        if (j.status === 'complete') {
          clearInterval(intervalRef.current)
          setPolling(false)
          if (j.report_id) {
            const r = await api.getReport(j.report_id)
            setReport(r)
          }
        } else if (j.status === 'error') {
          clearInterval(intervalRef.current)
          setPolling(false)
          setError(j.error || 'Analysis failed')
        }
      } catch (e) {
        clearInterval(intervalRef.current)
        setPolling(false)
        setError(e.message)
      }
    }

    tick()
    intervalRef.current = setInterval(tick, 2000)
    return () => clearInterval(intervalRef.current)
  }, [jobId])

  return { job, report, polling, error }
}
