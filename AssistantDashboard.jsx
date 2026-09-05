import React from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'

export default function AssistantDashboard(){
  return (
    <div>
      <Navbar />
      <div className="container flex gap-6 mt-6">
        <Sidebar />
        <main className="flex-1">
          <div className="card p-4">
            <h3 className="text-lg font-semibold">Assistant Dashboard</h3>
            <p className="text-sm text-muted">Help professors review and edit generated questions.</p>
          </div>
        </main>
      </div>
    </div>
  )
}
