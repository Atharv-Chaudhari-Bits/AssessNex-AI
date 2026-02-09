import React, {useState} from 'react'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function UploadPage(){
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState([])

  const handleFileUpload = async (e) => {
    const fileList = Array.from(e.target.files)
    
    if (fileList.length === 0) return

    setUploading(true)
    const uploadResults = []

    for (const file of fileList) {
      try {
        const formData = new FormData()
        formData.append('file', file)

        let result
        if (file.name.endsWith('.pdf')) {
          result = await api.documents.parsePdf(formData)
        } else if (file.name.endsWith('.docx')) {
          result = await api.documents.parseDocx(formData)
        } else if (file.name.endsWith('.txt')) {
          const text = await file.text()
          result = { data: { text: text, pageCount: 1 } }
        } else {
          toast.error(`Unsupported file type: ${file.name}`)
          continue
        }

        uploadResults.push({
          fileName: file.name,
          size: file.size,
          type: file.type,
          status: 'success',
          data: result.data,
          pages: result.data.pageCount || 1,
          textLength: result.data.text?.length || 0
        })
        
        toast.success(`✅ ${file.name} parsed successfully!`)
      } catch (err) {
        console.error(`Error processing ${file.name}:`, err)
        uploadResults.push({
          fileName: file.name,
          size: file.size,
          status: 'error',
          error: err.message || 'Failed to parse file'
        })
        toast.error(`❌ Failed to process ${file.name}`)
      }
    }

    setResults(uploadResults)
    setFiles(fileList)
    setUploading(false)
  }

  const downloadExtractedText = (result) => {
    if (!result.data?.text) return
    
    const blob = new Blob([result.data.text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${result.fileName.split('.')[0]}_extracted.txt`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('Text downloaded!')
  }

  const clearResults = () => {
    setResults([])
    setFiles([])
  }

  return (
    <div>
      <Navbar />
      <div className="container flex gap-6 mt-6 pb-8">
        <Sidebar />
        <main className="flex-1">
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-1">📤 Upload Documents</h2>
            <p className="text-slate-600 dark:text-slate-400">Upload and parse PDF, DOCX, or TXT files to extract text</p>
          </div>

          {/* Upload Area */}
          <div className="card p-8 mb-4 border-2 border-dashed border-slate-300 dark:border-slate-700 text-center">
            <label className="cursor-pointer">
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
              />
              <div className="space-y-2">
                <div className="text-4xl">📁</div>
                <p className="text-lg font-semibold">Drag & drop files here or click to select</p>
                <p className="text-sm text-slate-600 dark:text-slate-400">Supported: PDF, DOCX, TXT</p>
              </div>
            </label>
          </div>

          {uploading && (
            <div className="card p-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-center">
              <div className="spinner inline-block animate-spin w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full"></div>
              <p className="mt-3 text-blue-900 dark:text-blue-100">Processing files...</p>
            </div>
          )}

          {/* Results */}
          {results.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">📊 Upload Results ({results.length})</h3>
                <button
                  onClick={clearResults}
                  className="btn btn-sm btn-ghost"
                >
                  ✕ Clear
                </button>
              </div>

              {results.map((result, idx) => (
                <div key={idx} className={`card p-4 border-l-4 ${
                  result.status === 'success' 
                    ? 'border-green-500 bg-green-50 dark:bg-green-900/20' 
                    : 'border-red-500 bg-red-50 dark:bg-red-900/20'
                }`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xl">
                          {result.fileName.endsWith('.pdf') ? '📄' :
                           result.fileName.endsWith('.docx') ? '📝' :
                           '📋'}
                        </span>
                        <span className="font-semibold">{result.fileName}</span>
                        {result.status === 'success' && (
                          <span className="badge badge-success">✓ Success</span>
                        )}
                        {result.status === 'error' && (
                          <span className="badge badge-error">✗ Error</span>
                        )}
                      </div>

                      {result.status === 'success' && (
                        <div className="grid grid-cols-4 gap-3 mt-3 text-sm">
                          <div className="bg-white dark:bg-slate-800 p-3 rounded">
                            <p className="text-slate-600 dark:text-slate-400 text-xs">Size</p>
                            <p className="font-bold text-lg">{(result.size / 1024).toFixed(1)} KB</p>
                          </div>
                          <div className="bg-white dark:bg-slate-800 p-3 rounded">
                            <p className="text-slate-600 dark:text-slate-400 text-xs">Pages</p>
                            <p className="font-bold text-lg">{result.pages}</p>
                          </div>
                          <div className="bg-white dark:bg-slate-800 p-3 rounded">
                            <p className="text-slate-600 dark:text-slate-400 text-xs">Text Length</p>
                            <p className="font-bold text-lg">{result.textLength} chars</p>
                          </div>
                          <div className="bg-white dark:bg-slate-800 p-3 rounded">
                            <p className="text-slate-600 dark:text-slate-400 text-xs">Type</p>
                            <p className="font-bold text-lg">{result.type.split('/')[1]?.toUpperCase() || 'File'}</p>
                          </div>
                        </div>
                      )}

                      {result.status === 'error' && (
                        <p className="text-sm text-red-700 dark:text-red-300 mt-2">
                          {result.error || 'Failed to process file'}
                        </p>
                      )}
                    </div>

                    {result.status === 'success' && (
                      <button
                        onClick={() => downloadExtractedText(result)}
                        className="btn btn-sm btn-info ml-3"
                      >
                        📥 Download Text
                      </button>
                    )}
                  </div>

                  {/* Preview */}
                  {result.status === 'success' && result.data?.text && (
                    <details className="mt-3 border-t border-slate-200 dark:border-slate-700 pt-3">
                      <summary className="cursor-pointer font-medium text-sm text-slate-700 dark:text-slate-300">
                        📄 Preview Extracted Text
                      </summary>
                      <div className="mt-2 bg-white dark:bg-slate-800 p-3 rounded max-h-64 overflow-y-auto text-sm text-slate-600 dark:text-slate-400">
                        {result.data.text.substring(0, 500)}...
                      </div>
                    </details>
                  )}
                </div>
              ))}

              {/* Summary */}
              <div className="card p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-blue-800 dark:text-blue-200">Total Files</p>
                    <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{results.length}</p>
                  </div>
                  <div>
                    <p className="text-sm text-blue-800 dark:text-blue-200">Successful</p>
                    <p className="text-2xl font-bold text-green-700 dark:text-green-300">{results.filter(r => r.status === 'success').length}</p>
                  </div>
                  <div>
                    <p className="text-sm text-blue-800 dark:text-blue-200">Failed</p>
                    <p className="text-2xl font-bold text-red-700 dark:text-red-300">{results.filter(r => r.status === 'error').length}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Info */}
          {results.length === 0 && !uploading && (
            <div className="card p-6 bg-slate-50 dark:bg-slate-800/50">
              <h4 className="font-semibold mb-2">💡 How it works:</h4>
              <ul className="text-sm space-y-1 text-slate-600 dark:text-slate-400">
                <li>✓ Upload PDF, DOCX, or TXT files</li>
                <li>✓ Automatic text extraction and parsing</li>
                <li>✓ Download extracted text for further use</li>
                <li>✓ Use extracted content for document-based question generation</li>
              </ul>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
