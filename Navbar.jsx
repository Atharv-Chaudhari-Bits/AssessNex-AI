import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { LogOut, Menu, Search } from 'lucide-react'
import useAuthStore from '../store/useAuthStore'
import AvatarMenu from './AvatarMenu'

export default function Navbar(){
  const logout = useAuthStore(s => s.logout)
  const user = useAuthStore(s => s.user)
  const nav = useNavigate()

  return (
    <motion.header initial={{y:-20,opacity:0}} animate={{y:0,opacity:1}} className="w-full app-header-gradient">
      <div className="container flex items-center justify-between py-4">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-2xl font-semibold text-primary tracking-tight">AssessNex</Link>
          <span className="text-sm text-muted hidden sm:block">AI Exam Generator</span>
        </div>

        <div className="flex-1 px-6 hidden md:flex items-center">
          <label htmlFor="site-search" className="sr-only">Search content</label>
          <div className="flex items-center gap-2 w-full max-w-md p-1 bg-white card">
            <Search size={16} className="ml-2 text-muted" />
            <input id="site-search" placeholder="Search pages, exams, questions..." className="input text-sm border-0" />
          </div>
        </div>

        <div className="flex items-center gap-4">
          {user && <div className="hidden md:block text-sm text-slatey">{user.name} • <span className="text-muted">{user.role}</span></div>}
          <AvatarMenu/>
          <button aria-label="Logout" title="Logout" onClick={()=>{ logout(); nav('/login') }} className="ml-2 btn btn-sm btn-primary">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </motion.header>
  )
}
