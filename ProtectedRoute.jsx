import React from 'react'
import { Navigate } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'

export default function ProtectedRoute({ children, roles=[] }){
  const token = useAuthStore(s => s.token)
  const user = useAuthStore(s => s.user)

  if(!token) return <Navigate to="/login" replace />
  if(roles && roles.length>0 && user && !roles.includes(user.role)){
    // redirect to role dashboard
    const route = user.role === 'Professor' ? '/professor' : user.role === 'Assistant' ? '/assistant' : '/student'
    return <Navigate to={route} replace />
  }

  return children
}
