import React, {useState, useRef, useEffect} from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import api from '../services/api'
import DocumentChatBox from '../components/DocumentChatBox'
import Modal from '../components/Modal'
import toast from 'react-hot-toast'
import { Mail } from 'lucide-react'

export default function GeneratePage(){
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('document')
  
  // Manual generation form state
  const [subject, setSubject] = useState('Machine Learning')
  const [questionType, setQuestionType] = useState('Multiple Choice')
  const [difficulty, setDifficulty] = useState('Medium')
  const [numQuestions, setNumQuestions] = useState(5)
  const [subjects, setSubjects] = useState([])
  const [questionTypes, setQuestionTypes] = useState([])
  
  // Email state
  const [emailOpen, setEmailOpen] = useState(false)
  const [recipient, setRecipient] = useState('')
  const [emailLoading, setEmailLoading] = useState(false)
  
  const previewRef = useRef()

  // Load metadata on mount
  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const info = await api.questions.getInfo()
        if (info) {
          setQuestionTypes(Object.keys(info.question_types || {}) || ['Multiple Choice', 'Short Answer', 'Long Answer'])
          setSubjects(info.subjects || ['Machine Learning', 'Data Science', 'Python', 'General'])
        }
      } catch (err) {
        console.error('Failed to load metadata:', err)
        setQuestionTypes(['Multiple Choice', 'Short Answer', 'Long Answer', 'Essay', 'Code'])
        setSubjects(['Machine Learning', 'Data Science', 'Python', 'General'])
      }
    }
    loadMetadata()
  }, [])

  const handleQuestionsGenerated = (qs) => {
    setQuestions(qs || [])
    toast.success(`Generated ${(qs || []).length} questions!`)
  }

  // Manual generation
  const handleManualGenerate = async () => {
    if (!subject || !questionType) {
      toast.error('Please select subject and question type')
      return
    }

    setLoading(true)
    try {
      const result = await api.questions.generate(
        subject,
        questionType,
        difficulty,
        numQuestions
      )

      if (result && result.data) {
        setQuestions(Array.isArray(result.data) ? result.data : result.data.questions || [])
        toast.success(`Generated ${(result.data || []).length} questions!`)
      } else {
        throw new Error('No questions returned')
      }
    } catch (err) {
      console.error('Generation failed:', err)
      toast.error(err.message || 'Failed to generate questions')
    } finally {
      setLoading(false)
    }
  }

  // Export functions
  const downloadAsJSON = () => {
    if (questions.length === 0) {
      toast.error('No questions to download')
      return
    }
    const json = JSON.stringify(questions, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `questions_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Downloaded as JSON')
  }

  const downloadAsText = () => {
    if (questions.length === 0) {
      toast.error('No questions to download')
      return
    }
    let text = `QUESTION PAPER\n${'='.repeat(60)}\n\n`
    questions.forEach((q, i) => {
      text += `${i + 1}. ${q.question_text || q.text || 'Question'}\n`
      if (q.options) {
        q.options.forEach((opt, j) => {
          text += `   ${String.fromCharCode(65 + j)}) ${opt}\n`
        })
      }
      if (q.answer) {
        text += `   Answer: ${q.answer}\n`
      }
      if (q.explanation) {
        text += `   Explanation: ${q.explanation}\n`
      }
      text += '\n'
    })
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `questions_${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Downloaded as Text')
  }

  const copyToClipboard = () => {
    if (questions.length === 0) {
      toast.error('No questions to copy')
      return
    }
    let text = ''
    questions.forEach((q, i) => {
      text += `${i + 1}. ${q.question_text || q.text || 'Question'}\n`
      if (q.options) {
        q.options.forEach((opt, j) => {
          text += `${String.fromCharCode(65 + j)}) ${opt}\n`
        })
      }
      text += '\n'
    })
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard!')
  }

  return (
    <div>
      <Navbar />
      <div className="container flex gap-6 mt-6 pb-8">
        <Sidebar />
        <main className="flex-1">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-1">Generate Questions</h2>
            <p className="text-slate-600 dark:text-slate-400">AI-powered question generation from documents or manual parameters</p>
          </div>

          {/* Tabs */}
          <div className="card p-0 mb-4 overflow-hidden">
            <div className="flex border-b border-slate-200 dark:border-slate-700">
              <button
                onClick={() => setActiveTab('document')}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'document'
                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-b-2 border-blue-500'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`}
              >
                📄 Document-Based
              </button>
              <button
                onClick={() => setActiveTab('manual')}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'manual'
                    ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 border-b-2 border-blue-500'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`}
              >
                ⚙️ Manual
              </button>
            </div>
          </div>

          {/* Document-Based Tab */}
          {activeTab === 'document' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2">
                <DocumentChatBox
                  onQuestionsGenerated={handleQuestionsGenerated}
                />
              </div>
              <div className="card p-4 h-fit sticky top-4">
                <h4 className="font-semibold mb-3">📋 Actions</h4>
                <div className="space-y-2">
                  <button
                    onClick={copyToClipboard}
                    disabled={questions.length === 0}
                    className="w-full btn btn-sm btn-outline"
                  >
                    📋 Copy
                  </button>
                  <button
                    onClick={downloadAsJSON}
                    disabled={questions.length === 0}
                    className="w-full btn btn-sm btn-outline"
                  >
                    📥 JSON
                  </button>
                  <button
                    onClick={downloadAsText}
                    disabled={questions.length === 0}
                    className="w-full btn btn-sm btn-outline"
                  >
                    📄 Text
                  </button>
                  <button
                    onClick={() => setEmailOpen(true)}
                    disabled={questions.length === 0}
                    className="w-full btn btn-sm btn-primary"
                  >
                    📧 Email
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Manual Generation Tab */}
          {activeTab === 'manual' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="lg:col-span-2 space-y-4">
                {/* Configuration */}
                <div className="card p-4">
                  <h3 className="font-semibold mb-4">⚙️ Configuration</h3>
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Subject</label>
                      <select
                        value={subject}
                        onChange={(e) => setSubject(e.target.value)}
                        className="w-full input input-bordered text-sm"
                      >
                        {subjects.map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Question Type</label>
                      <select
                        value={questionType}
                        onChange={(e) => setQuestionType(e.target.value)}
                        className="w-full input input-bordered text-sm"
                      >
                        {questionTypes.map(t => (
                          <option key={t} value={t}>{t}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Difficulty</label>
                      <select
                        value={difficulty}
                        onChange={(e) => setDifficulty(e.target.value)}
                        className="w-full input input-bordered text-sm"
                      >
                        <option value="Easy">Easy</option>
                        <option value="Medium">Medium</option>
                        <option value="Hard">Hard</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Count</label>
                      <input
                        type="number"
                        min="1"
                        max="50"
                        value={numQuestions}
                        onChange={(e) => setNumQuestions(Number(e.target.value))}
                        className="w-full input input-bordered text-sm"
                      />
                    </div>
                  </div>
                  <button
                    onClick={handleManualGenerate}
                    disabled={loading}
                    className="w-full btn btn-primary"
                  >
                    {loading ? '⏳ Generating...' : '✨ Generate Questions'}
                  </button>
                </div>

                {/* Generated Questions */}
                <div className="card p-4">
                  <h3 className="font-semibold mb-3">❓ Generated ({questions.length})</h3>
                  <div className="space-y-3">
                    {questions.length === 0 && (
                      <div className="text-center text-slate-500 py-8">
                        <div className="text-3xl mb-2">📝</div>
                        <p className="text-sm">Questions will appear here</p>
                      </div>
                    )}
                    {questions.map((q, idx) => (
                      <div key={q.id || idx} className="border border-slate-200 dark:border-slate-700 rounded-lg p-3">
                        <div className="font-medium text-sm mb-2">
                          <span className="inline-block bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs mr-2">
                            {idx + 1}
                          </span>
                          {q.question_text || q.text}
                        </div>

                        {q.options && (
                          <div className="ml-4 space-y-1 mt-2">
                            {q.options.map((opt, i) => (
                              <div key={i} className="text-xs text-slate-600 dark:text-slate-400">
                                {String.fromCharCode(65 + i)}) {opt}
                              </div>
                            ))}
                          </div>
                        )}

                        {q.answer && (
                          <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                            <div className="text-xs font-medium text-green-700 dark:text-green-400">
                              ✅ Answer: {q.answer}
                            </div>
                          </div>
                        )}

                        <div className="flex gap-2 mt-2 text-xs text-slate-500">
                          {q.difficulty && (
                            <span className={`px-2 py-1 rounded ${
                              q.difficulty === 'Easy' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200' :
                              q.difficulty === 'Medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200' :
                              'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200'
                            }`}>
                              {q.difficulty}
                            </span>
                          )}
                          {q.question_type && (
                            <span className="bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 px-2 py-1 rounded">
                              {q.question_type}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Sidebar Actions */}
              <div className="card p-4 h-fit sticky top-4">
                <h4 className="font-semibold mb-3">📋 Actions</h4>
                <div className="space-y-2">
                  <button
                    onClick={copyToClipboard}
                    disabled={questions.length === 0}
                    className="w-full btn btn-sm btn-outline"
                  >
                    📋 Copy
                  </button>
                  <button
                    onClick={downloadAsJSON}
                    disabled={questions.length === 0}
                    className="w-full btn btn-sm btn-outline"
                  >
                    📥 JSON
                  </button>
                  <button
                    onClick={downloadAsText}
                    disabled={questions.length === 0}
                    className="w-full btn btn-sm btn-outline"
                  >
                    📄 Text
                  </button>
                  <button
                    onClick={() => setEmailOpen(true)}
                    disabled={questions.length === 0}
                    className="w-full btn btn-sm btn-primary"
                  >
                    📧 Email
                  </button>
                </div>

                <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                  <h5 className="text-sm font-medium mb-2">📊 Stats</h5>
                  <div className="space-y-1 text-xs text-slate-600 dark:text-slate-400">
                    <div>Total: {questions.length} questions</div>
                    <div>Subject: {subject}</div>
                    <div>Type: {questionType}</div>
                    <div>Level: {difficulty}</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Email Modal */}
          {emailOpen && (
            <Modal open={emailOpen} onClose={() => setEmailOpen(false)} title="📧 Email Questions">
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Recipient Email</label>
                  <input
                    type="email"
                    value={recipient}
                    onChange={(e) => setRecipient(e.target.value)}
                    placeholder="professor@example.com"
                    className="w-full input input-bordered text-sm"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      if (!recipient) {
                        toast.error('Please enter email')
                        return
                      }
                      setEmailLoading(true)
                      // Mock email send
                      setTimeout(() => {
                        toast.success(`Email sent to ${recipient}!`)
                        setEmailOpen(false)
                        setRecipient('')
                        setEmailLoading(false)
                      }, 1000)
                    }}
                    disabled={emailLoading || !recipient}
                    className="btn btn-primary btn-sm flex-1"
                  >
                    {emailLoading ? '⏳ Sending...' : '📧 Send'}
                  </button>
                  <button
                    onClick={() => setEmailOpen(false)}
                    className="btn btn-outline btn-sm flex-1"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </Modal>
          )}
        </main>
      </div>
    </div>
  )
}
