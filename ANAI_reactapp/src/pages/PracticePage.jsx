import React, {useEffect, useState} from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function PracticePage(){
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [subject, setSubject] = useState('Machine Learning')
  const [subjects, setSubjects] = useState([])
  const [selectedAnswers, setSelectedAnswers] = useState({})

  useEffect(() => {
    const loadSubjects = async () => {
      try {
        const subj = await api.questions.getSubjects?.()
        if (Array.isArray(subj)) {
          setSubjects(subj)
        } else {
          setSubjects(['Machine Learning', 'Data Science', 'Python', 'General'])
        }
      } catch (err) {
        setSubjects(['Machine Learning', 'Data Science', 'Python', 'General'])
      }
    }
    loadSubjects()
  }, [])

  const loadQuestions = async () => {
    setLoading(true)
    try {
      const result = await api.questions.generate(
        subject,
        'Multiple Choice',
        'Medium',
        10
      )
      
      if (result && result.data) {
        setQuestions(Array.isArray(result.data) ? result.data : result.data.questions || [])
        setSelectedAnswers({})
        toast.success(`Loaded ${(Array.isArray(result.data) ? result.data : result.data.questions || []).length} practice questions!`)
      }
    } catch (err) {
      console.error('Failed to load questions:', err)
      toast.error('Failed to load practice questions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (subjects.length > 0) {
      loadQuestions()
    }
  }, [])

  const handleAnswerSelect = (questionId, answer) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }))
  }

  const download = (q, idx) => {
    const text = `Question ${idx + 1}: ${q.question_text || q.text}\n\n`
      + (q.options ? q.options.map((opt, i) => `${String.fromCharCode(65 + i)}) ${opt}`).join('\n') + '\n\n' : '')
      + (q.answer ? `Answer: ${q.answer}\n` : '')
      + (q.explanation ? `Explanation: ${q.explanation}` : '')
    
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `question-${q.id || idx}.txt`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Question downloaded!')
  }

  return (
    <div>
      <Navbar />
      <div className="container flex gap-6 mt-6 pb-8">
        <Sidebar />
        <main className="flex-1">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-1">📚 Practice Questions</h2>
            <p className="text-slate-600 dark:text-slate-400">Test your knowledge with practice questions</p>
          </div>

          {/* Subject Selector */}
          <div className="card p-4 mb-4 flex items-center gap-3">
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="input input-bordered flex-1"
            >
              {subjects.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button
              onClick={loadQuestions}
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? '⏳ Loading...' : '🔄 Load Questions'}
            </button>
          </div>

          {/* Questions Display */}
          {loading ? (
            <div className="card p-8 text-center">
              <div className="text-3xl mb-2">⏳</div>
              <p className="text-slate-500">Loading practice questions...</p>
            </div>
          ) : questions.length === 0 ? (
            <div className="card p-8 text-center">
              <div className="text-3xl mb-2">📝</div>
              <p className="text-slate-500">No questions available</p>
            </div>
          ) : (
            <div className="space-y-4">
              {questions.map((q, idx) => (
                <div key={q.id || idx} className="card p-4 border border-slate-200 dark:border-slate-700">
                  {/* Question Text */}
                  <div className="mb-3">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-semibold text-sm flex-1">
                        <span className="inline-block bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs mr-2">
                          Q{idx + 1}
                        </span>
                        {q.question_text || q.text}
                      </h3>
                      <button
                        onClick={() => download(q, idx)}
                        className="btn btn-ghost btn-xs ml-2"
                        title="Download question"
                      >
                        📥
                      </button>
                    </div>
                  </div>

                  {/* Options */}
                  {q.options && q.options.length > 0 && (
                    <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-3 mb-3">
                      <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">Select your answer:</p>
                      <div className="space-y-2">
                        {q.options.map((option, optIdx) => (
                          <label key={optIdx} className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              name={`question-${q.id || idx}`}
                              value={String.fromCharCode(65 + optIdx)}
                              checked={selectedAnswers[q.id || idx] === String.fromCharCode(65 + optIdx)}
                              onChange={() => handleAnswerSelect(q.id || idx, String.fromCharCode(65 + optIdx))}
                              className="w-4 h-4"
                            />
                            <span className="text-sm">
                              <span className="font-medium">{String.fromCharCode(65 + optIdx)})</span> {option}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Answer & Explanation (Collapsible) */}
                  {(q.answer || q.explanation) && (
                    <details className="border-t border-slate-200 dark:border-slate-700 pt-3">
                      <summary className="cursor-pointer text-sm font-medium text-green-700 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300">
                        ✅ Show Answer & Explanation
                      </summary>
                      <div className="mt-2 space-y-2 text-sm">
                        {q.answer && (
                          <div>
                            <p className="font-medium text-green-700 dark:text-green-400">Correct Answer: {q.answer}</p>
                            {selectedAnswers[q.id || idx] && (
                              <p className={selectedAnswers[q.id || idx] === q.answer ? 'text-green-600' : 'text-red-600'}>
                                Your Answer: {selectedAnswers[q.id || idx]}
                                {selectedAnswers[q.id || idx] === q.answer ? ' ✅' : ' ❌'}
                              </p>
                            )}
                          </div>
                        )}
                        {q.explanation && (
                          <div>
                            <p className="font-medium text-slate-700 dark:text-slate-300">Explanation:</p>
                            <p className="text-slate-600 dark:text-slate-400">{q.explanation}</p>
                          </div>
                        )}
                      </div>
                    </details>
                  )}

                  {/* Metadata */}
                  <div className="flex gap-2 mt-3 text-xs text-slate-500">
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

              {/* Summary */}
              <div className="card p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-blue-900 dark:text-blue-100">📊 Your Progress</p>
                    <p className="text-sm text-blue-800 dark:text-blue-200 mt-1">
                      Answered: {Object.keys(selectedAnswers).length} / {questions.length}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                      {Math.round((Object.keys(selectedAnswers).length / questions.length) * 100)}%
                    </p>
                    <p className="text-xs text-blue-600 dark:text-blue-400">Complete</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
