import React, { useState, useEffect, useRef } from 'react'
import { Send, Trash2, Download, Copy, Settings } from 'lucide-react'
import api from '../services/api'

const CustomizedQAPage = () => {
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('Medium')
  const [bloomLevels, setBloomLevels] = useState(['Remember', 'Understand', 'Apply'])
  const [chatMessages, setChatMessages] = useState([])
  const [userInput, setUserInput] = useState('')
  const [generatedQuestions, setGeneratedQuestions] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedQuestion, setExpandedQuestion] = useState(null)
  const chatEndRef = useRef(null)

  const bloomOptions = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']
  const difficultyLevels = ['Easy', 'Medium', 'Hard']

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const toggleBloomLevel = (level) => {
    setBloomLevels(prev =>
      prev.includes(level)
        ? prev.filter(l => l !== level)
        : [...prev, level]
    )
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    
    if (!topic.trim()) {
      alert('Please enter a chat topic')
      return
    }

    if (!userInput.trim()) {
      return
    }

    // Add user message to chat
    const userMessage = { role: 'user', content: userInput }
    setChatMessages(prev => [...prev, userMessage])
    setUserInput('')

    setLoading(true)
    try {
      const response = await api.questions.customized(
        topic,
        difficulty,
        bloomLevels,
        userInput,
        'Multiple Choice'
      )

      if (response.data && response.data.length > 0) {
        const question = response.data[0]
        
        // Add AI response
        const aiMessage = {
          role: 'assistant',
          content: `Generated question with ${difficulty} difficulty for "${bloomLevels.join(', ')}" levels`
        }
        setChatMessages(prev => [...prev, aiMessage])

        // Add to generated questions
        setGeneratedQuestions(prev => [...prev, {
          id: Date.now(),
          question: question.question || question.text,
          options: question.options || [],
          answer: question.answer || '',
          bloomLevel: userInput,
          timestamp: new Date().toLocaleTimeString()
        }])
      } else {
        const errorMessage = {
          role: 'assistant',
          content: 'Could not generate question. Please try again.'
        }
        setChatMessages(prev => [...prev, errorMessage])
      }
    } catch (error) {
      console.error('Error:', error)
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.message || 'Failed to generate question'}`
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleCopyQuestion = (questionText) => {
    navigator.clipboard.writeText(questionText)
    alert('Question copied to clipboard!')
  }

  const handleRemoveQuestion = (id) => {
    setGeneratedQuestions(prev => prev.filter(q => q.id !== id))
  }

  const handleClearAll = () => {
    if (window.confirm('Clear all questions and chat history?')) {
      setGeneratedQuestions([])
      setChatMessages([])
    }
  }

  const handleExportJSON = () => {
    const data = {
      topic,
      difficulty,
      bloomLevels,
      questions: generatedQuestions,
      exportedAt: new Date().toISOString()
    }
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `customized_questions_${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
            <Settings className="w-8 h-8 text-blue-400" />
            Customised Q&A Generation
          </h1>
          <p className="text-gray-400">Chat-based question generation with Bloom's Taxonomy levels</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Sidebar - Configuration */}
          <div className="lg:col-span-1">
            <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
              <h2 className="text-xl font-semibold mb-4">Configuration</h2>

              {/* Chat Topic */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">Chat Topic</label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., Machine Learning, Database Design"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-400"
                />
              </div>

              {/* Difficulty Level */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">Difficulty Level</label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-blue-400"
                >
                  {difficultyLevels.map(level => (
                    <option key={level} value={level}>{level}</option>
                  ))}
                </select>
              </div>

              {/* Bloom's Taxonomy */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-3">Bloom's Taxonomy Levels</label>
                <div className="space-y-2">
                  {bloomOptions.map(level => (
                    <label key={level} className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={bloomLevels.includes(level)}
                        onChange={() => toggleBloomLevel(level)}
                        className="w-4 h-4 rounded border-slate-600 accent-blue-400"
                      />
                      <span className="text-sm">{level}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Section - Chat and Questions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Chat Interface */}
            <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden flex flex-col h-96">
              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatMessages.length === 0 && (
                  <div className="flex items-center justify-center h-full text-gray-400">
                    <p>Start chatting to generate customised questions!</p>
                  </div>
                )}
                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-gray-100'
                    }`}>
                      <p className="text-sm">{msg.content}</p>
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Chat Input */}
              <div className="border-t border-slate-700 p-4">
                <form onSubmit={handleSendMessage} className="flex gap-2">
                  <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="Ask for questions, modify topics..."
                    disabled={loading}
                    className="flex-1 px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-400 disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={loading || !topic.trim()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </div>

            {/* Generated Questions */}
            {generatedQuestions.length > 0 && (
              <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold">Generated Questions ({generatedQuestions.length})</h3>
                  <button
                    onClick={handleClearAll}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Clear All
                  </button>
                </div>

                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {generatedQuestions.map((q) => (
                    <div
                      key={q.id}
                      className="bg-slate-700 rounded-lg p-4 border border-slate-600 hover:border-blue-400 transition"
                    >
                      <div
                        onClick={() => setExpandedQuestion(expandedQuestion === q.id ? null : q.id)}
                        className="cursor-pointer"
                      >
                        <p className="text-sm font-medium text-gray-300 mb-2">{q.question}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs bg-blue-600/50 text-blue-200 px-2 py-1 rounded">
                            {q.bloomLevel}
                          </span>
                          <span className="text-xs text-gray-400">{q.timestamp}</span>
                        </div>
                      </div>

                      {expandedQuestion === q.id && q.options.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-600">
                          <div className="space-y-2">
                            {q.options.map((opt, idx) => (
                              <label key={idx} className="flex items-center gap-2 text-sm">
                                <input type="radio" name={`q-${q.id}`} className="w-4 h-4" />
                                {opt}
                              </label>
                            ))}
                          </div>
                          {q.answer && (
                            <p className="mt-3 text-xs text-green-400">
                              Answer: {q.answer}
                            </p>
                          )}
                        </div>
                      )}

                      <div className="mt-3 flex gap-2 justify-end">
                        <button
                          onClick={() => handleCopyQuestion(q.question)}
                          className="px-2 py-1 bg-slate-600 hover:bg-slate-500 rounded text-xs flex items-center gap-1"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => handleRemoveQuestion(q.id)}
                          className="px-2 py-1 bg-red-600/50 hover:bg-red-600 rounded text-xs flex items-center gap-1"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Export Button */}
                <button
                  onClick={handleExportJSON}
                  className="mt-4 w-full px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Export as JSON
                </button>
              </div>
            )}

            {generatedQuestions.length === 0 && chatMessages.length === 0 && (
              <div className="bg-slate-800 rounded-lg p-8 border border-slate-700 text-center text-gray-400">
                <p>💡 Start chatting to generate customised questions!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CustomizedQAPage
