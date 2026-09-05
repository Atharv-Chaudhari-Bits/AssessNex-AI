import React, { useState, useRef, useEffect } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import config from '../config'

export default function DocumentChatBox({ onQuestionsGenerated, onDocumentLoaded }) {
  const [document, setDocument] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [documentLoading, setDocumentLoading] = useState(false)
  const [subject, setSubject] = useState('General')
  const [questionType, setQuestionType] = useState('Multiple Choice')
  const [difficulty, setDifficulty] = useState('Medium')
  const [subjects, setSubjects] = useState([])
  const [questionTypes, setQuestionTypes] = useState([])
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  // Load subjects and question types on mount
  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const info = await api.questions.getInfo?.()
        if (info) {
          setQuestionTypes(Object.keys(info.question_types || {}))
          setSubjects(info.subjects || ['General', 'Machine Learning', 'Data Science'])
        }
      } catch (err) {
        console.error('Failed to load metadata:', err)
      }
    }
    loadMetadata()
  }, [])

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle document upload (PDF, TXT, DOCX)
  const handleDocumentUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const validTypes = [
      'application/pdf',
      'text/plain',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]

    if (!validTypes.includes(file.type)) {
      toast.error('Only PDF, TXT, and DOCX files are supported')
      return
    }

    setDocumentLoading(true)
    try {
      // Parse document to extract text
      let extractedText = ''

      if (file.type === 'text/plain') {
        extractedText = await file.text()
      } else if (file.type === 'application/pdf') {
        // For PDF, we'll send to backend for processing
        const formData = new FormData()
        formData.append('file', file)
        const response = await fetch(`${config.API_BASE || 'http://localhost:8000/api/v1'}/documents/parse-pdf`, {
          method: 'POST',
          body: formData,
        })
        if (response.ok) {
          const data = await response.json()
          extractedText = data.text || ''
        } else {
          toast.error('Failed to parse PDF')
          return
        }
      } else if (file.name.endsWith('.docx')) {
        // For DOCX, we'll send to backend
        const formData = new FormData()
        formData.append('file', file)
        const response = await fetch(`${config.API_BASE || 'http://localhost:8000/api/v1'}/documents/parse-docx`, {
          method: 'POST',
          body: formData,
        })
        if (response.ok) {
          const data = await response.json()
          extractedText = data.text || ''
        } else {
          toast.error('Failed to parse DOCX')
          return
        }
      }

      if (extractedText.trim().length === 0) {
        toast.error('No text found in document')
        return
      }

      // Store document
      setDocument({
        name: file.name,
        type: file.type,
        text: extractedText,
        uploadedAt: new Date().toLocaleString(),
        wordCount: extractedText.split(/\s+/).length,
      })

      // Add to chat
      setMessages([
        ...messages,
        {
          type: 'system',
          content: `📄 Document loaded: **${file.name}** (${extractedText.split(/\s+/).length} words)`,
          timestamp: new Date(),
        },
      ])

      toast.success(`Document loaded successfully! Ready to generate questions.`)
      onDocumentLoaded?.(document)
    } catch (err) {
      console.error('Document upload error:', err)
      toast.error('Failed to process document')
    } finally {
      setDocumentLoading(false)
    }
  }

  // Handle question generation from document
  const handleGenerateQuestions = async (e) => {
    e.preventDefault()

    if (!document) {
      toast.error('Please upload a document first')
      return
    }

    if (!input.trim()) {
      toast.error('Please enter a question or topic')
      return
    }

    const userMessage = input.trim()
    setInput('')

    // Add user message to chat
    const newMessages = [
      ...messages,
      {
        type: 'user',
        content: userMessage,
        timestamp: new Date(),
      },
    ]
    setMessages(newMessages)

    setLoading(true)
    try {
      // Call backend to generate questions from document context
      const response = await fetch(`${config.API_BASE || 'http://localhost:8000/api/v1'}/documents/generate-questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_text: document.text,
          question_prompt: userMessage,
          subject: subject,
          question_type: questionType,
          difficulty_level: difficulty,
          num_questions: 5,
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to generate questions')
      }

      const result = await response.json()
      const questions = result.data || result.questions || []

      // Add AI response to chat
      const assistantMessage = {
        type: 'assistant',
        content: `Generated ${questions.length} questions based on your request:`,
        questions: questions,
        timestamp: new Date(),
      }

      setMessages([...newMessages, assistantMessage])
      onQuestionsGenerated?.(questions)
      toast.success(`Generated ${questions.length} questions!`)
    } catch (err) {
      console.error('Generation error:', err)

      // Add error message to chat
      setMessages([
        ...newMessages,
        {
          type: 'error',
          content: `❌ Error: ${err.message}`,
          timestamp: new Date(),
        },
      ])

      toast.error(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Clear chat and document
  const handleClear = () => {
    setMessages([])
    setDocument(null)
    setInput('')
    toast.success('Chat cleared')
  }

  // Copy document text to clipboard
  const handleCopyDocument = () => {
    if (document) {
      navigator.clipboard.writeText(document.text)
      toast.success('Document text copied to clipboard')
    }
  }

  return (
    <div className="card h-full flex flex-col bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-700 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-lg">📚 Document-Based Question Generation</h3>
          {document && (
            <button
              onClick={handleClear}
              className="btn btn-ghost btn-sm"
              title="Clear chat and document"
            >
              ✕
            </button>
          )}
        </div>

        {!document && (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Upload a document (PDF, TXT, DOCX) or paste text to generate contextual questions
          </p>
        )}

        {document && (
          <div className="bg-blue-50 dark:bg-blue-900/30 rounded-lg p-3 text-sm">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium text-blue-900 dark:text-blue-200">📄 {document.name}</div>
                <div className="text-blue-800 dark:text-blue-300 text-xs mt-1">
                  {document.wordCount} words • Loaded: {document.uploadedAt}
                </div>
              </div>
              <button
                onClick={handleCopyDocument}
                className="btn btn-ghost btn-xs"
                title="Copy document text"
              >
                📋 Copy
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Document Upload Section */}
      {!document && (
        <div className="border-b border-slate-200 dark:border-slate-700 p-4 space-y-3">
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium mb-2">Upload Document</label>
            <div className="flex gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.docx,.doc"
                onChange={handleDocumentUpload}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={documentLoading}
                className="btn btn-primary btn-sm flex-1"
              >
                {documentLoading ? 'Processing...' : '📁 Upload File'}
              </button>
            </div>
            <div className="text-xs text-slate-500 mt-2">
              Supported: PDF, TXT, DOCX (Max 10MB)
            </div>
          </div>

          {/* Or Paste Text */}
          <div>
            <label className="block text-sm font-medium mb-2">Or Paste Text Directly</label>
            <textarea
              placeholder="Paste document content here..."
              className="w-full p-3 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-sm resize-none"
              rows="4"
              onBlur={(e) => {
                if (e.target.value.trim()) {
                  const text = e.target.value.trim()
                  setDocument({
                    name: 'Pasted Text',
                    type: 'text/plain',
                    text: text,
                    uploadedAt: new Date().toLocaleString(),
                    wordCount: text.split(/\s+/).length,
                  })
                  setMessages([
                    {
                      type: 'system',
                      content: `📝 Text pasted: ${text.split(/\s+/).length} words`,
                      timestamp: new Date(),
                    },
                  ])
                  e.target.value = ''
                  toast.success('Text loaded successfully!')
                }
              }}
            />
          </div>
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 dark:bg-slate-800/50">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 dark:text-slate-400 py-8">
            <div className="text-4xl mb-2">💬</div>
            <p className="text-sm">Upload a document to get started</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : msg.type === 'error'
                  ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
                  : msg.type === 'system'
                  ? 'bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200'
                  : 'bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-600'
              }`}
            >
              <div className="text-sm">{msg.content}</div>
              {msg.questions && msg.questions.length > 0 && (
                <div className="mt-3 space-y-2">
                  {msg.questions.map((q, i) => (
                    <div key={i} className="text-xs bg-white/20 dark:bg-slate-800/50 p-2 rounded">
                      <div className="font-medium">{i + 1}. {q.question_text?.substring(0, 60)}...</div>
                    </div>
                  ))}
                </div>
              )}
              <div className="text-xs opacity-70 mt-1">{msg.timestamp?.toLocaleTimeString()}</div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Configuration & Input */}
      {document && (
        <div className="border-t border-slate-200 dark:border-slate-700 p-4 space-y-3">
          {/* Settings Row */}
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-xs font-medium mb-1">Subject</label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full input input-sm text-sm"
              >
                {subjects.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">Type</label>
              <select
                value={questionType}
                onChange={(e) => setQuestionType(e.target.value)}
                className="w-full input input-sm text-sm"
              >
                {questionTypes.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full input input-sm text-sm"
              >
                <option value="Easy">Easy</option>
                <option value="Medium">Medium</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
          </div>

          {/* Input Field */}
          <form onSubmit={handleGenerateQuestions} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask something about the document or specify what questions to generate..."
              className="flex-1 input input-bordered text-sm"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !document}
              className="btn btn-primary btn-sm"
            >
              {loading ? '⏳' : '→'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
