import React, {useEffect, useState} from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import { Link } from 'react-router-dom'
import api from '../services/api'

export default function ProfessorDashboard(){
  const [stats, setStats] = useState({
    totalQuestionsGenerated: 0,
    documentsProcessed: 0,
    examsCreated: 0,
    studentsEnrolled: 0,
    averageCompletion: 0,
    pendingReviews: 0
  })

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      setStats({
        totalQuestionsGenerated: 342,
        documentsProcessed: 28,
        examsCreated: 15,
        studentsEnrolled: 127,
        averageCompletion: 78,
        pendingReviews: 42
      })
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const recentExams = [
    {
      id: 1,
      title: 'Machine Learning Midterm',
      created: new Date(Date.now() - 604800000).toLocaleDateString(),
      questions: 20,
      students: 45,
      submissions: 38
    },
    {
      id: 2,
      title: 'Python Fundamentals Quiz',
      created: new Date(Date.now() - 1209600000).toLocaleDateString(),
      questions: 10,
      students: 67,
      submissions: 64
    },
    {
      id: 3,
      title: 'Data Science Assessment',
      created: new Date(Date.now() - 1814400000).toLocaleDateString(),
      questions: 30,
      students: 56,
      submissions: 56
    }
  ]

  return (
    <div>
      <Navbar />
      <div className="container flex gap-6 mt-6 pb-8">
        <Sidebar />
        <main className="flex-1">
          {/* Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-1">🎓 Professor Dashboard</h2>
            <p className="text-slate-600 dark:text-slate-400">Manage exams, questions, and student progress</p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="card p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 border border-blue-200 dark:border-blue-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-800 dark:text-blue-200">Questions Generated</p>
                  <p className="text-3xl font-bold text-blue-700 dark:text-blue-300 mt-1">{stats.totalQuestionsGenerated}</p>
                </div>
                <div className="text-4xl">📝</div>
              </div>
            </div>

            <div className="card p-4 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 border border-green-200 dark:border-green-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-800 dark:text-green-200">Exams Created</p>
                  <p className="text-3xl font-bold text-green-700 dark:text-green-300 mt-1">{stats.examsCreated}</p>
                </div>
                <div className="text-4xl">🎯</div>
              </div>
            </div>

            <div className="card p-4 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 border border-purple-200 dark:border-purple-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-800 dark:text-purple-200">Students Enrolled</p>
                  <p className="text-3xl font-bold text-purple-700 dark:text-purple-300 mt-1">{stats.studentsEnrolled}</p>
                </div>
                <div className="text-4xl">👥</div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <Link
              to="/generate"
              className="card p-6 hover:shadow-lg transition-shadow cursor-pointer bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <div className="flex items-center gap-4">
                <div className="text-4xl">✨</div>
                <div>
                  <h3 className="text-lg font-semibold">Generate Questions</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400">AI-powered question generation</p>
                </div>
              </div>
            </Link>

            <Link
              to="/exam-builder"
              className="card p-6 hover:shadow-lg transition-shadow cursor-pointer bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <div className="flex items-center gap-4">
                <div className="text-4xl">🎓</div>
                <div>
                  <h3 className="text-lg font-semibold">Build Exam</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Create exam papers easily</p>
                </div>
              </div>
            </Link>

            <Link
              to="/upload"
              className="card p-6 hover:shadow-lg transition-shadow cursor-pointer bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <div className="flex items-center gap-4">
                <div className="text-4xl">📤</div>
                <div>
                  <h3 className="text-lg font-semibold">Upload Documents</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Parse and process documents</p>
                </div>
              </div>
            </Link>
          </div>

          {/* Secondary Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <Link
              to="/review"
              className="card p-4 hover:shadow-lg transition-shadow cursor-pointer border-2 border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">Review Questions</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">Pending reviews: <span className="font-bold text-yellow-700 dark:text-yellow-300">{stats.pendingReviews}</span></p>
                </div>
                <div className="text-3xl">✅</div>
              </div>
            </Link>

            <div className="card p-4 bg-slate-50 dark:bg-slate-800/50">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">Documents Processed</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{stats.documentsProcessed} documents parsed</p>
                </div>
                <div className="text-3xl">📑</div>
              </div>
            </div>
          </div>

          {/* Recent Exams */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">📚 Recent Exams</h3>
              <Link to="/exam-builder" className="text-blue-600 dark:text-blue-400 text-sm hover:underline">
                View All →
              </Link>
            </div>

            <div className="space-y-3">
              {recentExams.map(exam => (
                <div key={exam.id} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="flex-1">
                    <p className="font-medium">{exam.title}</p>
                    <div className="flex gap-4 mt-1 text-xs text-slate-600 dark:text-slate-400">
                      <span>📅 {exam.created}</span>
                      <span>📝 {exam.questions} questions</span>
                      <span>👥 {exam.students} students</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{exam.submissions}/{exam.students}</p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {Math.round((exam.submissions / exam.students) * 100)}% submitted
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Stats Footer */}
          <div className="mt-6 p-4 bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800/50 dark:to-slate-800/30 rounded-lg border border-slate-200 dark:border-slate-700">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{stats.averageCompletion}%</p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Average Completion</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-700 dark:text-green-300">{stats.examsCreated}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Active Exams</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">{Math.round(stats.totalQuestionsGenerated / stats.examsCreated)}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">Avg Questions/Exam</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
