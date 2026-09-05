import React from 'react'
import { NavLink } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'
import { Home, Upload, FileText, Settings, BookOpen, MessageSquare } from 'lucide-react'

export default function Sidebar(){
  const user = useAuthStore(s => s.user)

  if(!user) return null
  const role = user.role

  return (
    <aside className="w-64 p-4 hidden lg:block">
      <div className="card p-4 space-y-4">
        <div className="text-sm font-semibold">Navigation</div>
        <nav className="space-y-2">
          <NavLink to={role === 'Professor' ? '/professor' : role === 'Assistant' ? '/assistant' : '/student'} className={({isActive})=> `flex items-center gap-3 p-3 rounded-md ${isActive? 'bg-primary/10 border border-primary/10':''} card-hover`} aria-current="page"> <Home size={16}/> Dashboard</NavLink>
          {(role==='Professor' || role==='Assistant') && <NavLink to="/upload" className={({isActive})=> `flex items-center gap-3 p-3 rounded-md ${isActive? 'bg-primary/10':''} card-hover`}> <Upload size={16}/> Upload</NavLink>}
          {(role==='Professor' || role==='Assistant') && <NavLink to="/parse" className={({isActive})=> `flex items-center gap-3 p-3 rounded-md ${isActive? 'bg-primary/10':''} card-hover`}> <FileText size={16}/> Parse</NavLink>}
          {role==='Professor' && <NavLink to="/generate" className={({isActive})=> `flex items-center gap-3 p-3 rounded-md ${isActive? 'bg-primary/10':''} card-hover`}> <BookOpen size={16}/> Generate</NavLink>}
          {role==='Professor' && <NavLink to="/exam-builder" className={({isActive})=> `flex items-center gap-3 p-3 rounded-md ${isActive? 'bg-primary/10':''} card-hover`}> <FileText size={16}/> Exam Builder</NavLink>}
          {(role==='Professor' || role==='Assistant') && <NavLink to="/customized-qa" className={({isActive})=> `flex items-center gap-3 p-3 rounded-md ${isActive? 'bg-primary/10':''} card-hover`}> <MessageSquare size={16}/> Customised Q&A</NavLink>}
          {role==='Student' && <NavLink to="/practice" className={({isActive})=> `flex items-center gap-3 p-3 rounded-md ${isActive? 'bg-primary/10':''} card-hover`}> <BookOpen size={16}/> Practice</NavLink>}
          <NavLink to="/settings" className={({isActive})=> `flex items-center gap-3 p-3 rounded-md ${isActive? 'bg-primary/10':''} card-hover`}> <Settings size={16}/> Settings</NavLink>
        </nav>
      </div>
    </aside>
  )
}
