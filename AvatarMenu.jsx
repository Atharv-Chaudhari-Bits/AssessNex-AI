import React, {useState, useRef, useEffect} from 'react'
import { User, ChevronDown } from 'lucide-react'
import { motion } from 'framer-motion'
import useAuthStore from '../store/useAuthStore'
import { useNavigate } from 'react-router-dom'

export default function AvatarMenu(){
  const user = useAuthStore(s => s.user)
  const logout = useAuthStore(s => s.logout)
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef()

  useEffect(()=>{
    function onDoc(e){ if(ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('click', onDoc)
    return ()=>document.removeEventListener('click', onDoc)
  },[])

  function onKey(e){ if(e.key === 'Escape') setOpen(false) }

  return (
    <div className="relative" ref={ref} onKeyDown={onKey}>
      <button aria-expanded={open} aria-haspopup="menu" onClick={()=>setOpen(v=>!v)} className="flex items-center gap-2 focus:outline-none">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white">{user ? user.name.charAt(0) : <User/>}</div>
        <ChevronDown size={14} />
      </button>
      {open && (
        <motion.div initial={{opacity:0, y:-6}} animate={{opacity:1, y:0}} exit={{opacity:0,y:-6}} className="absolute right-0 mt-2 bg-white card p-3 w-40" role="menu">
          <div className="text-sm mb-2">{user?.name}</div>
          <button role="menuitem" onClick={()=>{ setOpen(false); nav('/settings') }} className="w-full text-left p-2 rounded hover:bg-gray-50">Profile</button>
          <button role="menuitem" onClick={()=>{ logout(); nav('/login') }} className="w-full text-left p-2 rounded hover:bg-gray-50">Logout</button>
        </motion.div>
      )}
    </div>
  )
}
