import React, {useState} from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function ParsePage(){
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [loading, setLoading] = useState(false)
  const [extractedData, setExtractedData] = useState({
    text: '',
    pages: 0,
    concepts: [],
    summary: ''
  })

  const handleFileUpload = async (e) => {
    const uploadedFile = e.target.files?.[0]
    if (!uploadedFile) return

    setFile(uploadedFile)
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)

      let result
      if (uploadedFile.name.endsWith('.pdf')) {
        result = await api.documents.parsePdf(formData)
      } else if (uploadedFile.name.endsWith('.docx')) {
        result = await api.documents.parseDocx(formData)
      } else if (uploadedFile.name.endsWith('.txt')) {
        const text = await uploadedFile.text()
        result = { data: { text: text, pageCount: 1 } }
      } else {
        toast.error('Unsupported file type')
        return
      }

      setExtractedData({
        text: result.data.text || '',
        pages: result.data.pageCount || 1,
        concepts: [],
        summary: ''
      })

      setPreview(result.data.text || '')
      toast.success('✅ File parsed successfully!')

      // Try to extract concepts
      try {
        const conceptResult = await api.documents.extractConcepts(formData)
        if (conceptResult.data) {
          setExtractedData(prev => ({
            ...prev,
            concepts: Array.isArray(conceptResult.data) ? conceptResult.data : conceptResult.data.concepts || []
          }))
        }
      } catch (err) {
        console.log('Concepts extraction skipped')
      }

      // Try to summarize
      try {
        const summaryResult = await api.documents.summarize(formData)
        if (summaryResult.data) {
          setExtractedData(prev => ({
            ...prev,
            summary: summaryResult.data.summary || summaryResult.data || ''
          }))
        }
      } catch (err) {
        console.log('Summary extraction skipped')
      }
    } catch (err) {
      console.error('Error parsing file:', err)
      toast.error('Failed to parse file')
    } finally {
      setLoading(false)
    }
  }

  const downloadExtractedText = () => {
    if (!extractedData.text) return
    
    const blob = new Blob([extractedData.text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${file?.name?.split('.')[0] || 'extracted'}_text.txt`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Text downloaded!')
  }

  const downloadSummary = () => {
    if (!extractedData.summary) return
    
    const content = `File: ${file?.name}\n\nSUMMARY:\n${extractedData.summary}`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${file?.name?.split('.')[0] || 'document'}_summary.txt`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Summary downloaded!')
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(extractedData.text)
    toast.success('Copied to clipboard!')
  }

  return (
    <div>
      <Navbar />
      <div className="container flex gap-6 mt-6 pb-8">
        <Sidebar />
        <main className="flex-1">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-1">🔍 Document Parser (OCR)</h2>
            <p className="text-slate-600 dark:text-slate-400">Extract text, concepts, and summaries from documents</p>
          </div>

          {/* File Upload */}
          <div className="card p-6 mb-4 border-2 border-dashed border-slate-300 dark:border-slate-700">
            <label className="cursor-pointer">
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                disabled={loading}
                className="hidden"
              />
              <div className="text-center space-y-2">
                <div className="text-4xl">📄</div>
                <p className="text-lg font-semibold">Click to upload or drag & drop</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">Supported: PDF, DOCX, TXT</p>
              </div>
            </label>
          </div>

          {loading && (
            <div className="card p-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-center">
              <div className="animate-spin w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full inline-block"></div>
              <p className="mt-3 text-blue-900 dark:text-blue-100">Parsing document...</p>
            </div>
          )}

          {file && !loading && (
            <div className="space-y-4">
              {/* File Info */}
              <div className="card p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">
                      {file.name.endsWith('.pdf') ? '📕' : file.name.endsWith('.docx') ? '📗' : '📄'}
                    </span>
                    <div>
                      <p className="font-semibold">{file.name}</p>
                      <p className="text-sm text-slate-600 dark:text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-lg">{extractedData.pages}</p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">pages</p>
                  </div>
                </div>
              </div>

              {/* Stats & Actions */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card p-4 bg-blue-50 dark:bg-blue-900/20">
                  <p className="text-sm text-blue-800 dark:text-blue-200">Characters Extracted</p>
                  <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{extractedData.text.length}</p>
                </div>
                <div className="card p-4 bg-green-50 dark:bg-green-900/20">
                  <p className="text-sm text-green-800 dark:text-green-200">Words</p>
                  <p className="text-2xl font-bold text-green-700 dark:text-green-300">{extractedData.text.split(/\s+/).length}</p>
                </div>
                <div className="card p-4 bg-purple-50 dark:bg-purple-900/20">
                  <p className="text-sm text-purple-800 dark:text-purple-200">Concepts Found</p>
                  <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">{extractedData.concepts.length}</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={downloadExtractedText}
                  className="btn btn-sm btn-primary"
                >
                  📥 Download Text
                </button>
                {extractedData.summary && (
                  <button
                    onClick={downloadSummary}
                    className="btn btn-sm btn-info"
                  >
                    📝 Download Summary
                  </button>
                )}
                <button
                  onClick={copyToClipboard}
                  className="btn btn-sm btn-outline"
                >
                  📋 Copy to Clipboard
                </button>
                <label className="btn btn-sm btn-ghost">
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  📁 Change File
                </label>
              </div>

              {/* Concepts */}
              {extractedData.concepts.length > 0 && (
                <div className="card p-4">
                  <h3 className="font-semibold mb-3">🎯 Extracted Concepts</h3>
                  <div className="flex flex-wrap gap-2">
                    {extractedData.concepts.slice(0, 20).map((concept, idx) => (
                      <span key={idx} className="badge badge-lg badge-primary">
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Summary */}
              {extractedData.summary && (
                <div className="card p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                  <h3 className="font-semibold mb-2">📚 Summary</h3>
                  <p className="text-sm text-amber-900 dark:text-amber-100 leading-relaxed">
                    {extractedData.summary}
                  </p>
                </div>
              )}

              {/* Preview */}
              <details className="card p-4">
                <summary className="cursor-pointer font-semibold">📄 Full Text Preview</summary>
                <div className="mt-4 bg-slate-50 dark:bg-slate-800 p-3 rounded max-h-96 overflow-y-auto text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono">
                  {preview || 'No text extracted'}
                </div>
              </details>
            </div>
          )}

          {!file && !loading && (
            <div className="card p-6 bg-slate-50 dark:bg-slate-800/50">
              <h4 className="font-semibold mb-2">💡 Parser Features:</h4>
              <ul className="text-sm space-y-1 text-slate-600 dark:text-slate-400">
                <li>✓ Extract text from PDF, DOCX, and TXT files</li>
                <li>✓ Automatic concept extraction (AI-powered)</li>
                <li>✓ Document summarization</li>
                <li>✓ Character and word count statistics</li>
                <li>✓ Download extracted content in various formats</li>
              </ul>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
  )
}
