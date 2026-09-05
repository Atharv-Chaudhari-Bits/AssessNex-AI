import React, {useState} from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import useAuthStore from '../store/useAuthStore'
import { API_BASE, ENDPOINTS } from '../config'

export default function Settings(){
  const user = useAuthStore(s => s.user)
  const update = useAuthStore(s => s.updateProfile)
  const [name,setName] = useState(user?.name || '')
  const [email,setEmail] = useState(user?.email || '')

  const save = ()=>{
    update({ name, email })
    const raw = localStorage.getItem('assessnex_auth')
    if(raw){
      const obj = JSON.parse(raw)
      obj.user = { ...(obj.user||{}), name, email }
      localStorage.setItem('assessnex_auth', JSON.stringify(obj))
    }
  }

  return (
    <div>
      <Navbar />
      <div className="container flex gap-6 mt-6">
        <Sidebar />
        <main className="flex-1">
          <h3 className="text-lg font-semibold mb-3">Settings</h3>

          <div className="card p-4 mb-4">
            <div className="text-sm font-medium mb-2">Profile</div>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <input className="p-2 border rounded" value={name} onChange={e=>setName(e.target.value)} />
              <input className="p-2 border rounded" value={email} onChange={e=>setEmail(e.target.value)} />
            </div>
            <div className="mt-3 flex gap-2">
              <button onClick={save} className="btn btn-primary">Save</button>
            </div>
          </div>

          <div className="card p-4">
            <div className="text-sm font-medium mb-2">API Configuration</div>
            <div className="text-xs text-muted mb-2">Base: <code>{API_BASE}</code></div>
            <div className="text-xs text-muted">Endpoints:</div>
            <ul className="mt-2 text-sm space-y-1">
              {Object.entries(ENDPOINTS).map(([k,v])=> (
                <li key={k}><strong>{k}:</strong> <code>{typeof v === 'string' ? v : JSON.stringify(v)}</code></li>
              ))}
            </ul>
          </div>

        </main>
      </div>
    </div>
  )
}
