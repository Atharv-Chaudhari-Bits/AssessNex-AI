import React from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Login from './pages/Login'
import Register from './pages/Register'
import ProfessorDashboard from './pages/ProfessorDashboard'
import AssistantDashboard from './pages/AssistantDashboard'
import StudentDashboard from './pages/StudentDashboard'
import UploadPage from './pages/UploadPage'
import ParsePage from './pages/ParsePage'
import GeneratePage from './pages/GeneratePage'
import ReviewPage from './pages/ReviewPage'
import ExamBuilder from './pages/ExamBuilder'
import PracticePage from './pages/PracticePage'
import Settings from './pages/Settings'
import CustomizedQAPage from './pages/CustomizedQAPage'
import NotFound from './pages/NotFound'
import ProtectedRoute from './routes/ProtectedRoute'

export default function App(){
  const location = useLocation()

  const pageTransition = {
    initial: { opacity: 0, y: 8 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -8 }
  }

  return (
    <div className="min-h-screen">
      <AnimatePresence mode="wait">
        <motion.div key={location.pathname} initial="initial" animate="animate" exit="exit" variants={pageTransition} transition={{duration:0.28}} className="min-h-screen">
          <Routes location={location}>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<Login/>} />
            <Route path="/register" element={<Register/>} />

            <Route path="/professor" element={<ProtectedRoute roles={["Professor"]}><ProfessorDashboard/></ProtectedRoute>} />
            <Route path="/assistant" element={<ProtectedRoute roles={["Assistant"]}><AssistantDashboard/></ProtectedRoute>} />
            <Route path="/student" element={<ProtectedRoute roles={["Student"]}><StudentDashboard/></ProtectedRoute>} />

            <Route path="/upload" element={<ProtectedRoute roles={["Professor","Assistant"]}><UploadPage/></ProtectedRoute>} />
            <Route path="/parse" element={<ProtectedRoute roles={["Professor","Assistant"]}><ParsePage/></ProtectedRoute>} />
            <Route path="/generate" element={<ProtectedRoute roles={["Professor"]}><GeneratePage/></ProtectedRoute>} />
            <Route path="/review" element={<ProtectedRoute roles={["Professor","Assistant"]}><ReviewPage/></ProtectedRoute>} />
            <Route path="/exam-builder" element={<ProtectedRoute roles={["Professor"]}><ExamBuilder/></ProtectedRoute>} />
            <Route path="/practice" element={<ProtectedRoute roles={["Student"]}><PracticePage/></ProtectedRoute>} />
            <Route path="/customized-qa" element={<ProtectedRoute roles={["Professor","Assistant"]}><CustomizedQAPage/></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute roles={["Professor","Assistant","Student"]}><Settings/></ProtectedRoute>} />

            <Route path="*" element={<NotFound/>} />
          </Routes>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
