import axios from 'axios'
import config, { ENDPOINTS, makeMockUser } from '../config'

const apiClient = axios.create({
  baseURL: config.API_BASE,
  timeout: 120000,
  headers: { Accept: 'application/json' }
})

const withError = (error, operation) => {
  const message = error?.response?.data?.detail || error?.message || `Failed to ${operation}`
  const enriched = new Error(message)
  enriched.status = error?.response?.status
  enriched.cause = error
  throw enriched
}

const mockAuth = (role, email, name) => ({
  token: `demo-${role.toLowerCase()}-${Date.now()}`,
  user: makeMockUser(role, email, name)
})

const api = {
  endpoints: ENDPOINTS,

  auth: {
    login: async ({ email, password, role, name }) => {
      if (config.ENABLE_MOCK_AUTH) return { data: mockAuth(role, email, name) }
      try {
        const response = await apiClient.post('/auth/login', { email, password, role })
        return { data: { token: response.data.token || response.data.access_token, user: response.data.user } }
      } catch (error) {
        return withError(error, 'log in')
      }
    },
    register: async ({ name, email, password, role }) => {
      if (config.ENABLE_MOCK_AUTH) return { data: mockAuth(role, email, name) }
      try {
        const response = await apiClient.post('/auth/register', { name, email, password, role })
        return { data: { token: response.data.token || response.data.access_token, user: response.data.user } }
      } catch (error) {
        return withError(error, 'register')
      }
    },
    me: async (token) => {
      try {
        const response = await apiClient.get('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        return { data: { user: response.data.user || response.data } }
      } catch (error) {
        if (config.ENABLE_MOCK_AUTH) return { data: { user: makeMockUser('Student') } }
        return withError(error, 'load the current user')
      }
    }
  },

  upload: async (file) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiClient.post('/documents/parse-pdf', formData)
      return { data: response.data }
    } catch (error) {
      return withError(error, 'upload the document')
    }
  },

  questions: {
    generate: async (subject, questionType, difficultyLevel, count, context = '') => {
      try {
        const response = await apiClient.post('/questions/generate', {
          subject,
          question_type: questionType,
          difficulty_level: difficultyLevel,
          num_questions: count,
          additional_context: context
        })
        return { data: response.data }
      } catch (error) {
        return withError(error, 'generate questions')
      }
    },
    customized: async (topic, difficulty, bloomLevels, chatContext = '', questionType = 'Multiple Choice') => {
      try {
        const bloomLevel = Array.isArray(bloomLevels) ? bloomLevels[0] : bloomLevels
        const response = await apiClient.post('/questions/customized', {
          topic,
          bloom_level: bloomLevel || 'Understand',
          question_type: questionType,
          chat_context: chatContext,
          additional_context: difficulty ? `Requested difficulty: ${difficulty}` : null
        })
        return { data: response.data }
      } catch (error) {
        return withError(error, 'generate customized questions')
      }
    },
    getSubjects: async () => {
      try {
        const response = await apiClient.get('/questions/subjects')
        return { data: response.data }
      } catch (error) {
        return withError(error, 'load subjects')
      }
    },
    getInfo: async () => {
      try {
        const response = await apiClient.get('/questions/info')
        return { data: response.data }
      } catch (error) {
        return withError(error, 'load question information')
      }
    }
  },

  documents: {
    parsePdf: async (file) => {
      try {
        const formData = new FormData()
        formData.append('file', file)
        const response = await apiClient.post('/documents/parse-pdf', formData)
        return response.data
      } catch (error) {
        return withError(error, 'parse the PDF')
      }
    },
    parseDocx: async (file) => {
      try {
        const formData = new FormData()
        formData.append('file', file)
        const response = await apiClient.post('/documents/parse-docx', formData)
        return response.data
      } catch (error) {
        return withError(error, 'parse the DOCX')
      }
    },
    generateQuestions: async (documentText, prompt, subject, type, difficulty, count) => {
      try {
        const response = await apiClient.post('/documents/generate-questions', {
          document_text: documentText,
          question_prompt: prompt,
          subject,
          question_type: type,
          difficulty_level: difficulty,
          num_questions: count
        })
        return response.data
      } catch (error) {
        return withError(error, 'generate questions from the document')
      }
    },
    summarize: async (documentText) => {
      try {
        const response = await apiClient.post('/documents/summarize', { document_text: documentText })
        return response.data
      } catch (error) {
        return withError(error, 'summarize the document')
      }
    },
    extractConcepts: async (documentText) => {
      try {
        const response = await apiClient.post('/documents/extract-concepts', { document_text: documentText })
        return response.data
      } catch (error) {
        return withError(error, 'extract concepts')
      }
    }
  }
}

export default api
