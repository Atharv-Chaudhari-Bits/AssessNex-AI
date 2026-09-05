import React, {useEffect, useState} from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import { Link } from 'react-router-dom'
import api from '../services/api'

export default function StudentDashboard(){
  const [stats, setStats] = useState({
    totalQuestionsPracticed: 0,
    correctAnswers: 0,
    accuracy: 0,
    assignmentsPending: 0,
    assignmentsSubmitted: 0,
    averageScore: 0
  })

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      // Simulate loading dashboard stats
      setStats({
        totalQuestionsPracticed: 45,
        correctAnswers: 38,
        accuracy: 84.4,
        assignmentsPending: 3,
        assignmentsSubmitted: 7,
        averageScore: 78
      })
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const recentActivities = [
    {
      id: 1,
      type: 'practice',
      title: 'Machine Learning Quiz',
      date: new Date(Date.now() - 3600000).toLocaleString(),
      score: 8,
      outOf: 10
    },
    {
      id: 2,
      type: 'assignment',
      title: 'Data Science Assignment 1',
      date: new Date(Date.now() - 86400000).toLocaleString(),
      score: 85,
      outOf: 100
    },
    {
      id: 3,
      type: 'practice',
      title: 'Python Programming Test',
      date: new Date(Date.now() - 172800000).toLocaleString(),
      score: 9,
      outOf: 10
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
            <h2 className="text-2xl font-bold mb-1">👋 Welcome back!</h2>
            <p className="text-slate-600 dark:text-slate-400">Keep practicing to improve your skills</p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="card p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 border border-blue-200 dark:border-blue-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-800 dark:text-blue-200">Questions Practiced</p>
                  <p className="text-3xl font-bold text-blue-700 dark:text-blue-300 mt-1">{stats.totalQuestionsPracticed}</p>
                </div>
                <div className="text-4xl">📚</div>
              </div>
            </div>

            <div className="card p-4 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 border border-green-200 dark:border-green-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-800 dark:text-green-200">Accuracy</p>
                  <p className="text-3xl font-bold text-green-700 dark:text-green-300 mt-1">{stats.accuracy}%</p>
                </div>
                <div className="text-4xl">🎯</div>
              </div>
            </div>

            <div className="card p-4 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 border border-purple-200 dark:border-purple-700">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-800 dark:text-purple-200">Average Score</p>
                  <p className="text-3xl font-bold text-purple-700 dark:text-purple-300 mt-1">{stats.averageScore}</p>
                </div>
                <div className="text-4xl">⭐</div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <Link
              to="/practice"
              className="card p-6 hover:shadow-lg transition-shadow cursor-pointer bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <div className="flex items-center gap-4">
                <div className="text-4xl">📝</div>
                <div>
                  <h3 className="text-lg font-semibold">Practice Questions</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Solve practice questions to improve</p>
                </div>
              </div>
            </Link>

            <Link
              to="/parse"
              className="card p-6 hover:shadow-lg transition-shadow cursor-pointer bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <div className="flex items-center gap-4">
                <div className="text-4xl">📤</div>
                <div>
                  <h3 className="text-lg font-semibold">Upload & Parse</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400">Upload study materials to parse</p>
                </div>
              </div>
            </Link>
          </div>

          {/* Assignments Stats */}
          <div className="card p-4 mb-6">
            <h3 className="text-lg font-semibold mb-4">📋 Assignment Status</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.assignmentsPending}</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">Pending</p>
              </div>
              <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.assignmentsSubmitted}</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">Submitted</p>
              </div>
              <div className="text-center p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{Math.round((stats.assignmentsSubmitted / (stats.assignmentsPending + stats.assignmentsSubmitted)) * 100)}%</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">Completion</p>
              </div>
            </div>
          </div>

          {/* Recent Activities */}
          <div className="card p-4">
            <h3 className="text-lg font-semibold mb-4">📊 Recent Activities</h3>
            <div className="space-y-3">
              {recentActivities.map(activity => (
                <div key={activity.id} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border-l-4 border-blue-500">
                  <div>
                    <p className="font-medium text-sm">{activity.title}</p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{activity.date}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg">{activity.score}/{activity.outOf}</p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {Math.round((activity.score / activity.outOf) * 100)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
