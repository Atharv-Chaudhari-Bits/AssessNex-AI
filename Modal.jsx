import React from 'react'
import { motion } from 'framer-motion'

export default function Modal({open, onClose, title, children}){
  if(!open) return null
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" role="dialog" aria-modal="true">
      <motion.div initial={{scale:0.98,opacity:0}} animate={{scale:1,opacity:1}} className="w-full max-w-lg p-6 card">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-semibold text-lg">{title}</h3>
          <button onClick={onClose} className="text-sm text-muted btn btn-ghost">Close</button>
        </div>
        <div className="space-y-4">{children}</div>
      </motion.div>
    </div>
  )
}
