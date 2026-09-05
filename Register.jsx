import React, {useState} from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import useAuthStore from '../store/useAuthStore'
import toast from 'react-hot-toast'

export default function Register(){
  const [name,setName]=useState('')
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [role,setRole]=useState('Professor')
  const save = useAuthStore(s => s.saveToStorage)
  const nav = useNavigate()

  const submit = async (e)=>{
    e.preventDefault()
    try{
      const res = await api.auth.register({name,email,password,role})
      save(res.data.token, res.data.user)
      toast.success('Account created')
      const route = role === 'Professor' ? '/professor' : role === 'Assistant' ? '/assistant' : '/student'
      nav(route)
    }catch(err){ toast.error('Register failed') }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-soft">
      <div className="w-full max-w-md p-8 card">
        <h2 className="text-2xl font-semibold mb-3">Create account</h2>
        <p className="text-sm text-muted mb-4">Create an account to start generating exams with AI.</p>
        <form onSubmit={submit} className="space-y-3">
          <input placeholder="Full name" className="w-full p-2 border rounded" value={name} onChange={e=>setName(e.target.value)} />
          <input placeholder="Email" className="w-full p-2 border rounded" value={email} onChange={e=>setEmail(e.target.value)} />
          <input placeholder="Password" type="password" className="w-full p-2 border rounded" value={password} onChange={e=>setPassword(e.target.value)} />
          <select className="w-full p-2 border rounded" value={role} onChange={e=>setRole(e.target.value)}>
            <option>Professor</option>
            <option>Assistant</option>
            <option>Student</option>
          </select>
          <button className="w-full py-2 rounded btn btn-lg btn-accent">Create account</button>
        </form>
        <div className="mt-3 text-sm">Have an account? <Link to="/login" className="text-primary">Sign in</Link></div>
      </div>
    </div>
  )
}
