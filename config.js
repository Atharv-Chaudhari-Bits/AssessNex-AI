/** Central frontend configuration. */

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'
export const ENABLE_MOCK_AUTH = import.meta.env.VITE_ENABLE_MOCK_AUTH === 'true'

export const ENDPOINTS = {
  questions: {
    generate: `${API_BASE}/questions/generate`,
    customized: `${API_BASE}/questions/customized`,
    subjects: `${API_BASE}/questions/subjects`,
    info: `${API_BASE}/questions/info`
  },
  documents: {
    parsePdf: `${API_BASE}/documents/parse-pdf`,
    parseDocx: `${API_BASE}/documents/parse-docx`,
    generateQuestions: `${API_BASE}/documents/generate-questions`,
    summarize: `${API_BASE}/documents/summarize`,
    extractConcepts: `${API_BASE}/documents/extract-concepts`
  },
  papers: `${API_BASE}/papers/generate`,
  assignments: `${API_BASE}/documents/assignments/generate`
}

export function makeMockUser(role = 'Student', email = '', name = '') {
  const displayName = name || (role === 'Professor' ? 'Demo Professor' : role === 'Assistant' ? 'Demo Assistant' : 'Demo Student')
  return {
    id: `demo-${role.toLowerCase()}`,
    name: displayName,
    email: email || `${role.toLowerCase()}@example.com`,
    role
  }
}

export default { API_BASE, ENABLE_MOCK_AUTH, ENDPOINTS, makeMockUser }
