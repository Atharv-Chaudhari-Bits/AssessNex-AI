import axios from 'axios'
import config, { ENDPOINTS, makeMockUser } from '../config'

const apiClient = axios.create({ 
  baseURL: config.API_BASE || 'http://localhost:8000/api/v1',
  timeout: 30000
})

export default {
  endpoints: ENDPOINTS,
  auth: {
    login: async ({email, password, role, name}) => {
      try {
        const response = await apiClient.post('/auth/login', {
          email,
          password,
          role
        })
        return { data: { token: response.data.token || response.data.access_token, user: response.data.user || makeMockUser(role, email, name) } }
      } catch (err) {
        // Fallback to mock for development
        const token = `mock-jwt-${role}-${Date.now()}`
        return { data: { token, user: makeMockUser(role, email, name) } }
      }
    },
    register: async ({name, email, password, role}) => {
      try {
        const response = await apiClient.post('/auth/register', {
          name,
          email,
          password,
          role
        })
        return { data: { token: response.data.token || response.data.access_token, user: response.data.user || makeMockUser(role, email, name) } }
      } catch (err) {
        // Fallback to mock for development
        const token = `mock-jwt-${role}-${Date.now()}`
        return { data: { token, user: makeMockUser(role, email, name) } }
      }
    },
    me: async (token) => {
      try {
        const response = await apiClient.get('/auth/me', {
          headers: { Authorization: `Bearer ${token}` }
        })
        return { data: { user: response.data.user } }
      } catch (err) {
        // Fallback to mock
        const parts = token.split('-')
        const role = parts[2] || 'Student'
        return { data: { user: makeMockUser(role) } }
      }
    }
  },
  upload: async (file) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiClient.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      return { data: response.data }
    } catch (err) {
      // Fallback to mock
      return { data: { id: Date.now(), name: file?.name || 'document.pdf', size: file?.size||12345, status: 'uploaded' } }
    }
  },
  parse: async (fileId) => {
    try {
      const response = await apiClient.get(`/parse/${fileId}`)
      return { data: response.data }
    } catch (err) {
      // Fallback to mock
      return { data: { text: `Extracted text preview for file ${fileId}...\n1. What is X?\n2. Explain Y.\n3. Solve Z.` } }
    }
  },
  generate: async ({docs, settings}) => {
    try {
      const response = await apiClient.post('/questions/generate', {
        documents: docs,
        ...settings
      })
      return { data: response.data }
    } catch (err) {
      // Fallback to mock
      const questions = Array.from({length:5}).map((_,i)=>({ id: i+1, text: `Generated question ${i+1}`, difficulty: ['Easy','Medium','Hard'][i%3] }))
      return { data: { questions } }
    }
  },
  questions: {
    getInfo: async () => {
      try {
        const response = await apiClient.get('/questions/info')
        return response.data
      } catch (err) {
        console.error('Failed to get question info:', err)
        return {
          question_types: ['Multiple Choice', 'Short Answer', 'Long Answer', 'Fill Blank', 'Code'],
          subjects: ['Machine Learning', 'Data Science', 'Python', 'General']
        }
      }
    },
    generate: async (subject, type, difficulty, count, context = '') => {
      try {
        const response = await apiClient.post('/questions/generate', {
          subject,
          question_type: type,
          difficulty_level: difficulty,
          num_questions: count,
          additional_context: context
        })
        return response.data
      } catch (err) {
        console.error('Failed to generate questions:', err)
        throw err
      }
    },
    getSubjects: async () => {
      try {
        const response = await apiClient.get('/questions/subjects')
        return response.data.subjects || []
      } catch (err) {
        console.error('Failed to get subjects:', err)
        return ['Machine Learning', 'Data Science', 'Python', 'General']
      }
    },
    getAll: async () => {
      try {
        const response = await apiClient.get('/questions')
        return { data: response.data }
      } catch (err) {
        const q = Array.from({length:8}).map((_,i)=>({ id: i+1, text: `Sample question ${i+1}`, choices: [], answer: null }))
        return { data: q }
      }
    }
  },
  documents: {
    parsePdf: async (file) => {
      try {
        const formData = new FormData()
        formData.append('file', file)
        const response = await apiClient.post('/documents/parse-pdf', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        return response.data
      } catch (err) {
        console.error('Failed to parse PDF:', err)
        throw err
      }
    },
    parseDocx: async (file) => {
      try {
        const formData = new FormData()
        formData.append('file', file)
        const response = await apiClient.post('/documents/parse-docx', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        return response.data
      } catch (err) {
        console.error('Failed to parse DOCX:', err)
        throw err
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
      } catch (err) {
        console.error('Failed to generate questions from document:', err)
        throw err
      }
    },
    summarize: async (documentText) => {
      try {
        const response = await apiClient.post('/documents/summarize', {
          document_text: documentText
        })
        return response.data
      } catch (err) {
        console.error('Failed to summarize document:', err)
        throw err
      }
    },
    extractConcepts: async (documentText) => {
      try {
        const response = await apiClient.post('/documents/extract-concepts', {
          document_text: documentText
        })
        return response.data
      } catch (err) {
        console.error('Failed to extract concepts:', err)
        throw err
      }
    }
  },
  saveExam: async (payload) => {
    try {
      const response = await apiClient.post('/exams/save', payload)
      return { data: response.data }
    } catch (err) {
      // Fallback to mock
      return { data: { id: Date.now(), ...payload, status: 'saved' } }
    }
  },
  sendEmail: async ({to, subject, body, attachment}) => {
    try {
      const response = await apiClient.post('/email/send', {
        to,
        subject,
        body,
        attachment
      })
      return { data: response.data }
    } catch (err) {
      // Fallback to mock
      return { data: { status: 'sent', to, subject } }
    }
  },
  student: {
    questions: async (studentId) => {
      try {
        const response = await apiClient.get(`/student/${studentId}/questions`)
        return { data: response.data }
      } catch (err) {
        // Fallback to mock
        const q = Array.from({length:6}).map((_,i)=>({ id: i+1, text: `Practice question ${i+1}`, difficulty: ['Easy','Medium'][i%2] }))
        return { data: q }
      }
    }
  },
  questions: {
    generate: async (subject, questionType, difficulty, count, context) => {
      try {
        const response = await apiClient.post('/questions/generate', {
          subject, question_type: questionType, difficulty, count, additional_context: context
        })
        return { data: response.data }
      } catch (err) {
        return { data: { questions: [] } }
      }
    },
    customized: async (topic, difficulty, bloomLevels, chatContext, questionType = 'Multiple Choice') => {
      try {
        const params = new URLSearchParams({
          topic,
          difficulty,
          bloom_levels: bloomLevels.join(','),
          chat_context: chatContext,
          question_type: questionType
        })
        const response = await apiClient.post(`/questions/customized?${params}`)
        return { data: response.data }
      } catch (err) {
        console.error('Error generating customized question:', err)
        return { data: { questions: [], error: err.message } }
      }
    },
    getSubjects: async () => {
      try {
        const response = await apiClient.get('/questions/subjects')
        return { data: response.data }
      } catch (err) {
        return { data: { subjects: [] } }
      }
    },
    getInfo: async () => {
      try {
        const response = await apiClient.get('/questions/info')
        return { data: response.data }
      } catch (err) {
        return { data: { question_types: [], difficulty_levels: [] } }
      }
    }
  }
}
