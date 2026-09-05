import React, {useEffect, useState} from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function ExamBuilder(){
  const [examTitle, setExamTitle] = useState('Untitled Exam')
  const [description, setDescription] = useState('')
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState(null)
  const [subject, setSubject] = useState('Machine Learning')
  const [subjects, setSubjects] = useState(['Machine Learning', 'Data Science', 'Python', 'General'])
  const [examDuration, setExamDuration] = useState(60)
  const [totalMarks, setTotalMarks] = useState(100)

  useEffect(() => {
    loadAvailableQuestions()
  }, [subject])

  const loadAvailableQuestions = async () => {
    setLoading(true)
    try {
      const result = await api.questions.generate(subject, 'Multiple Choice', 'Medium', 15)
      const qList = Array.isArray(result.data) ? result.data : result.data.questions || []
      setQuestions(qList.map((q, idx) => ({
        ...q,
        id: q.id || `q-${idx}`,
        selected: false,
        marks: 1
      })))
    } catch (err) {
      toast.error('Failed to load questions')
      setQuestions([])
    } finally {
      setLoading(false)
    }
  }

  const toggleQuestion = (questionId) => {
    setQuestions(prev => prev.map(q =>
      q.id === questionId ? {...q, selected: !q.selected} : q
    ))
  }

  const updateMarks = (questionId, marks) => {
    setQuestions(prev => prev.map(q =>
      q.id === questionId ? {...q, marks: parseInt(marks) || 1} : q
    ))
  }

  const removeQuestion = (questionId) => {
    setQuestions(prev => prev.filter(q => q.id !== questionId))
  }

  const saveExam = async () => {
    const selectedQuestions = questions.filter(q => q.selected)
    
    if (!examTitle.trim()) {
      toast.error('Please enter exam title')
      return
    }
    
    if (selectedQuestions.length === 0) {
      toast.error('Please select at least one question')
      return
    }

    setLoading(true)
    try {
      const examData = {
        title: examTitle,
        description: description,
        subject: subject,
        duration: examDuration,
        totalMarks: totalMarks,
        questions: selectedQuestions.map(q => ({
          id: q.id,
          question_text: q.question_text || q.text,
          marks: q.marks,
          difficulty: q.difficulty,
          type: q.question_type
        }))
      }

      setSaved(examData)
      toast.success(`Exam "${examTitle}" created with ${selectedQuestions.length} questions!`)
      
      // Reset form
      setExamTitle('Untitled Exam')
      setDescription('')
      setQuestions(prev => prev.map(q => ({...q, selected: false})))
    } catch (err) {
      toast.error('Failed to save exam')
    } finally {
      setLoading(false)
    }
  }

  const exportExam = () => {
    const selectedQuestions = questions.filter(q => q.selected)
    const examJson = JSON.stringify({
      title: examTitle,
      description: description,
      subject: subject,
      duration: examDuration,
      totalMarks: totalMarks,
      questions: selectedQuestions.map(q => ({
        question_text: q.question_text || q.text,
        options: q.options || [],
        answer: q.answer,
        explanation: q.explanation,
        marks: q.marks,
        difficulty: q.difficulty,
        type: q.question_type
      }))
    }, null, 2)

    const blob = new Blob([examJson], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${examTitle.replace(/\s+/g, '_')}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Exam exported!')
  }

  const selectedCount = questions.filter(q => q.selected).length
  const totalMarksCalculated = questions.filter(q => q.selected).reduce((sum, q) => sum + (q.marks || 1), 0)

  return (
    <div>
      <Navbar />
      <div className="container flex gap-6 mt-6 pb-8">
        <Sidebar />
        <main className="flex-1">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-1">🎯 Exam Builder</h2>
            <p className="text-slate-600 dark:text-slate-400">Create and customize exams from questions</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Main Editor */}
            <div className="lg:col-span-2">
              {/* Exam Details */}
              <div className="card p-4 mb-4 space-y-3">
                <div>
                  <label className="label text-sm font-medium">Exam Title</label>
                  <input
                    type="text"
                    value={examTitle}
                    onChange={(e) => setExamTitle(e.target.value)}
                    placeholder="Enter exam title"
                    className="input input-bordered w-full"
                  />
                </div>

                <div>
                  <label className="label text-sm font-medium">Description</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Exam description (optional)"
                    className="textarea textarea-bordered w-full"
                    rows="2"
                  />
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="label text-sm font-medium">Subject</label>
                    <select
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      className="select select-bordered w-full"
                    >
                      {subjects.map(s => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="label text-sm font-medium">Duration (min)</label>
                    <input
                      type="number"
                      value={examDuration}
                      onChange={(e) => setExamDuration(parseInt(e.target.value) || 60)}
                      min="15"
                      max="480"
                      className="input input-bordered w-full"
                    />
                  </div>

                  <div>
                    <label className="label text-sm font-medium">Total Marks</label>
                    <input
                      type="number"
                      value={totalMarks}
                      onChange={(e) => setTotalMarks(parseInt(e.target.value) || 100)}
                      min="10"
                      max="1000"
                      className="input input-bordered w-full"
                    />
                  </div>
                </div>
              </div>

              {/* Questions List */}
              <div className="card p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Available Questions</h3>
                  <button
                    onClick={loadAvailableQuestions}
                    disabled={loading}
                    className="btn btn-sm btn-ghost"
                  >
                    🔄 Reload
                  </button>
                </div>

                {loading ? (
                  <div className="p-8 text-center text-slate-500">Loading questions...</div>
                ) : questions.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">No questions available</div>
                ) : (
                  <div className="space-y-3">
                    {questions.map((q, idx) => (
                      <div key={q.id} className={`border-l-4 p-3 rounded ${
                        q.selected ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-slate-300 dark:border-slate-700'
                      }`}>
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            checked={q.selected}
                            onChange={() => toggleQuestion(q.id)}
                            className="checkbox checkbox-primary mt-1"
                          />
                          <div className="flex-1">
                            <p className="font-medium text-sm mb-1">{q.question_text || q.text}</p>
                            <div className="flex gap-2 flex-wrap">
                              {q.difficulty && (
                                <span className="badge badge-sm badge-outline">{q.difficulty}</span>
                              )}
                              {q.question_type && (
                                <span className="badge badge-sm badge-outline">{q.question_type}</span>
                              )}
                            </div>
                          </div>
                          {q.selected && (
                            <div className="flex items-center gap-2">
                              <label className="label text-xs font-medium">Marks:</label>
                              <input
                                type="number"
                                value={q.marks}
                                onChange={(e) => updateMarks(q.id, e.target.value)}
                                min="1"
                                max="10"
                                className="input input-bordered input-sm w-16"
                              />
                            </div>
                          )}
                          <button
                            onClick={() => removeQuestion(q.id)}
                            className="btn btn-ghost btn-xs text-red-500"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Sidebar Summary */}
            <div className="space-y-4">
              {/* Stats */}
              <div className="card p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30">
                <h4 className="font-semibold mb-3 text-blue-900 dark:text-blue-100">📊 Exam Summary</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Selected Questions:</span>
                    <span className="font-bold text-lg text-blue-700 dark:text-blue-300">{selectedCount}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Marks:</span>
                    <span className="font-bold text-lg text-green-700 dark:text-green-300">{totalMarksCalculated}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Duration:</span>
                    <span className="font-bold">{examDuration} min</span>
                  </div>
                  <div className="border-t border-blue-300 dark:border-blue-700 my-2 pt-2">
                    <div className="flex justify-between">
                      <span>Difficulty Distribution:</span>
                    </div>
                    <div className="text-xs mt-1 space-y-1">
                      <div>Easy: {questions.filter(q => q.selected && q.difficulty === 'Easy').length}</div>
                      <div>Medium: {questions.filter(q => q.selected && q.difficulty === 'Medium').length}</div>
                      <div>Hard: {questions.filter(q => q.selected && q.difficulty === 'Hard').length}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="card p-4 space-y-2">
                <button
                  onClick={saveExam}
                  disabled={selectedCount === 0 || loading}
                  className="btn btn-primary w-full"
                >
                  ✅ Create Exam
                </button>
                <button
                  onClick={exportExam}
                  disabled={selectedCount === 0}
                  className="btn btn-outline w-full"
                >
                  📥 Export JSON
                </button>
              </div>

              {/* Success Message */}
              {saved && (
                <div className="card p-4 bg-green-50 dark:bg-green-900/20 border border-green-300 dark:border-green-700">
                  <p className="text-sm text-green-800 dark:text-green-200">
                    ✅ Exam <strong>{saved.title}</strong> created successfully with <strong>{saved.questions.length}</strong> questions!
                  </p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
