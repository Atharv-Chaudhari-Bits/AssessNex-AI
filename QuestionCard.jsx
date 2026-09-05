import React from 'react'
import { motion } from 'framer-motion'
import { Edit3, Check } from 'lucide-react'

export default function QuestionCard({q, onEdit, onApprove}){
  return (
    <motion.div whileHover={{ y: -4 }} className="p-4 card card-quiet animate-fade-up">
      <div className="flex justify-between items-start">
        <div className="pr-4">
          <div className="font-medium leading-tight text-gray-900">{q.text}</div>
          <div className="text-xs text-muted mt-2">Difficulty: {q.difficulty || 'Medium'}</div>
        </div>
        <div className="flex gap-2 items-center">
          <button aria-label="Edit question" onClick={()=>onEdit && onEdit(q)} className="btn btn-sm btn-ghost">
            <Edit3 size={14} />
            <span className="hidden sm:inline">Edit</span>
          </button>
          <button aria-label="Approve question" onClick={()=>onApprove && onApprove(q)} className="btn btn-sm btn-primary">
            <Check size={14} />
            <span className="hidden sm:inline">Approve</span>
          </button>
        </div>
      </div>
    </motion.div>
  )
}
