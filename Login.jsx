import React, {useState, useEffect} from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../services/api'
import useAuthStore from '../store/useAuthStore'
import toast from 'react-hot-toast'

export default function Login(){
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [role,setRole]=useState('Professor')
  const save = useAuthStore(s => s.saveToStorage)
  const load = useAuthStore(s => s.loadFromStorage)
  const nav = useNavigate()

  useEffect(()=>{ load() },[])

  const submit = async (e)=>{
    e.preventDefault()
    try{
      const res = await api.auth.login({email,password,role})
      save(res.data.token, res.data.user)
      toast.success('Logged in')
      const route = role === 'Professor' ? '/professor' : role === 'Assistant' ? '/assistant' : '/student'
      nav(route)
    }catch(err){ toast.error('Login failed') }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-soft">
      <div className="w-full max-w-md p-8 card">
        <h2 className="text-2xl font-semibold mb-3">Welcome back</h2>
        <p className="text-sm text-muted mb-4">Sign in to manage exams and generate questions.</p>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="text-sm">Email</label>
            <input className="w-full p-2 border rounded mt-1" value={email} onChange={e=>setEmail(e.target.value)} />
          </div>
          <div>
            <label className="text-sm">Password</label>
            <input type="password" className="w-full p-2 border rounded mt-1" value={password} onChange={e=>setPassword(e.target.value)} />
          </div>
          <div>
            <label className="text-sm">Role</label>
            <select className="w-full p-2 border rounded mt-1" value={role} onChange={e=>setRole(e.target.value)}>
              <option>Professor</option>
              <option>Assistant</option>
              <option>Student</option>
            </select>
          </div>
          <button className="w-full py-2 rounded btn btn-lg btn-primary">Sign in</button>
        </form>
        <div className="mt-3 text-sm">New? <Link to="/register" className="text-primary">Create an account</Link></div>
      </div>
    </div>
  )
}
