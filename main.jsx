import React, { useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'
import { Toaster } from 'react-hot-toast'
import useAuthStore from './store/useAuthStore'

function Root(){
  const load = useAuthStore(s => s.loadFromStorage)
  useEffect(()=>{ load() },[load])
  return <App />
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <Root />
      <Toaster position="top-right" />
    </BrowserRouter>
  </React.StrictMode>
)
