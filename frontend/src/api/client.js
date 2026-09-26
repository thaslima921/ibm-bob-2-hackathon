/**
 * API client for ChangeGuard backend.
 * Uses Vite proxy so all requests go to /analysis and /reports without CORS issues.
 */

const BASE = ''  // proxied by Vite dev server

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
  return res.json()
}

export const api = {
  // ---- repository ----
  scanRepository: (repositoryPath, description = '') =>
    request('/repository/scan', {
      method: 'POST',
      body: JSON.stringify({ repository_path: repositoryPath, description }),
    }),

  getRepository: (scanId) => request(`/repository/${scanId}`),

  getRepositoryChanges: (scanId) => request(`/repository/${scanId}/changes`),

  // ---- analysis ----
  startAnalysis: (diffId, diffText, label, repositoryId = null, projectDescription = '') =>
    request('/analysis', {
      method: 'POST',
      body: JSON.stringify({
        diff_id: diffId,
        diff_text: diffText,
        label,
        repository_id: repositoryId,
        project_description: projectDescription,
      }),
    }),

  getAnalysis: (jobId) => request(`/analysis/${jobId}`),

  // ---- reports ----
  listReports: () => request('/reports'),

  getReport: (reportId) => request(`/reports/${reportId}`),
}
