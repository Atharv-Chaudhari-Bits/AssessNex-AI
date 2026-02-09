import React, {useEffect, useState} from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function ReviewPage(){
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('pending')
  const [subject, setSubject] = useState('All')
  const [subjects, setSubjects] = useState(['All', 'Machine Learning', 'Data Science', 'Python', 'General'])

  useEffect(() => {
    loadQuestions()
  }, [filter, subject])

  const loadQuestions = async () => {
    setLoading(true)
    try {
      let questions = []
      
      if (filter === 'pending') {
        // Get latest generated questions for review
        const result = await api.questions.generate('General', 'Multiple Choice', 'Medium', 20)
        questions = (Array.isArray(result.data) ? result.data : result.data.questions || [])
          .map((q, idx) => ({
            ...q,
            id: q.id || `generated-${idx}`,
            status: 'pending',
            createdAt: new Date().toISOString()
          }))
      } else if (filter === 'approved') {
        questions = [
          {
            id: 'app-1',
            question_text: 'What is Machine Learning?',
            options: ['A', 'B', 'C', 'D'],
            answer: 'A',
            explanation: 'Machine Learning is...',
            difficulty: 'Easy',
            question_type: 'Multiple Choice',
            status: 'approved',
            createdAt: new Date(Date.now() - 86400000).toISOString()
          }
        ]
      }

      if (subject !== 'All') {
        questions = questions.filter(q => (q.subject || 'General') === subject)
      }

      setQuestions(questions)
    } catch (err) {
      console.error('Failed to load questions:', err)
      toast.error('Failed to load questions')
    } finally {
      setLoading(false)
    }
  }

  const approveQuestion = async (questionId) => {
    try {
      const question = questions.find(q => q.id === questionId)
      if (question) {
        question.status = 'approved'
        setQuestions([...questions])
        toast.success('Question approved!')
      }
    } catch (err) {
      toast.error('Failed to approve question')
    }
  }

  const rejectQuestion = async (questionId) => {
    try {
      const question = questions.find(q => q.id === questionId)
      if (question) {
        question.status = 'rejected'
        setQuestions(questions.filter(q => q.id !== questionId))
        toast.success('Question rejected!')
      }
    } catch (err) {
      toast.error('Failed to reject question')
    }
  }

  const editQuestion = (questionId) => {
    const question = questions.find(q => q.id === questionId)
    if (question) {
      const newText = prompt('Edit question:', question.question_text)
      if (newText) {
        question.question_text = newText
        setQuestions([...questions])
        toast.success('Question updated!')
      }
    }
  }

  return (
    <div>
      <Navbar />
      <div className="container flex gap-6 mt-6 pb-8">
        <Sidebar />
        <main className="flex-1">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-1">✅ Question Review</h2>
            <p className="text-slate-600 dark:text-slate-400">Review and approve/reject generated questions</p>
          </div>

          {/* Filters */}
          <div className="card p-4 mb-4 flex flex-wrap items-center gap-3">
            <div className="flex gap-2">
              <button
                onClick={() => setFilter('pending')}
                className={`btn btn-sm ${filter === 'pending' ? 'btn-primary' : 'btn-ghost'}`}
              >
                ⏳ Pending ({questions.filter(q => q.status === 'pending').length})
              </button>
              <button
                onClick={() => setFilter('approved')}
                className={`btn btn-sm ${filter === 'approved' ? 'btn-primary' : 'btn-ghost'}`}
              >
                ✅ Approved
              </button>
            </div>

            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="input input-bordered input-sm flex-1"
            >
              {subjects.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Questions List */}
          {loading ? (
            <div className="card p-8 text-center">
              <p className="text-slate-500">Loading questions...</p>
            </div>
          ) : questions.length === 0 ? (
            <div className="card p-8 text-center">
              <p className="text-slate-500">No questions to review</p>
            </div>
          ) : (
            <div className="space-y-4">
              {questions.map((q, idx) => (
                <div key={q.id} className={`card p-4 border-2 ${
                  q.status === 'pending' ? 'border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20' :
                  q.status === 'approved' ? 'border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-900/20' :
                  'border-red-300 dark:border-red-700'
                }`}>
                  {/* Question Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="badge badge-lg">{idx + 1}</span>
                        {q.status === 'pending' && <span className="badge badge-warning">PENDING</span>}
                        {q.status === 'approved' && <span className="badge badge-success">APPROVED</span>}
                        {q.difficulty && (
                          <span className={`badge ${
                            q.difficulty === 'Easy' ? 'badge-success' :
                            q.difficulty === 'Medium' ? 'badge-warning' :
                            'badge-error'
                          }`}>
                            {q.difficulty}
                          </span>
                        )}
                      </div>
                      <p className="font-semibold text-sm mb-1">{q.question_text || q.text}</p>
                    </div>
                  </div>

                  {/* Options */}
                  {q.options && q.options.length > 0 && (
                    <div className="bg-slate-100 dark:bg-slate-800 rounded-lg p-3 mb-3 text-sm">
                      {q.options.map((opt, i) => (
                        <div key={i} className={`py-1 ${
                          String.fromCharCode(65 + i) === q.answer ? 'font-bold text-green-700 dark:text-green-400' : ''
                        }`}>
                          {String.fromCharCode(65 + i)}) {opt}
                          {String.fromCharCode(65 + i) === q.answer && ' ✓'}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Explanation */}
                  {q.explanation && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded p-2 mb-3 text-sm">
                      <p className="font-medium text-blue-900 dark:text-blue-200 mb-1">Explanation:</p>
                      <p className="text-blue-800 dark:text-blue-300">{q.explanation}</p>
                    </div>
                  )}

                  {/* Actions */}
                  {q.status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => approveQuestion(q.id)}
                        className="btn btn-sm btn-success flex-1"
                      >
                        ✅ Approve
                      </button>
                      <button
                        onClick={() => rejectQuestion(q.id)}
                        className="btn btn-sm btn-error flex-1"
                      >
                        ❌ Reject
                      </button>
                      <button
                        onClick={() => editQuestion(q.id)}
                        className="btn btn-sm btn-info flex-1"
                      >
                        ✏️ Edit
                      </button>
                    </div>
                  )}

                  {/* Date */}
                  {q.createdAt && (
                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                      {new Date(q.createdAt).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

function EditForm({q, onSave}){
  const [text, setText] = useState(q.text)
  return (
    <div>
      <textarea className="w-full p-2 border rounded" value={text} onChange={e=>setText(e.target.value)} />
      <div className="mt-3 flex justify-end">
        <button onClick={()=>onSave({...q, text})} className="btn btn-primary">Save</button>
      </div>
    </div>
  )
}
