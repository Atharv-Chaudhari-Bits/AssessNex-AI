import React, {useState, useRef} from 'react'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function FileUploader({onUploaded}){
  const [loading, setLoading] = useState(false)

  const fileRef = useRef()

  const onChange = async (e)=>{
    const file = e.target.files[0]
    if(!file) return
    setLoading(true)
    try{
      const res = await api.upload(file)
      toast.success('Uploaded')
      onUploaded && onUploaded(res.data)
    }catch(err){
      toast.error('Upload failed')
    }finally{ setLoading(false) }
  }

  return (
    <div className="p-4 card">
      <div className="mb-2 text-sm text-muted">Upload document</div>
      <input ref={fileRef} type="file" onChange={onChange} className="hidden" />
      <div className="mt-3 flex items-center gap-3">
        <button className="btn btn-primary btn-sm" onClick={(e)=>{ e.preventDefault(); fileRef.current && fileRef.current.click(); }}>
          Choose File
        </button>
        <button onClick={async()=>{
          // simulate upload from previously selected file if any
          if(!fileRef.current || !fileRef.current.files.length){ toast.error('No file selected'); return }
          setLoading(true)
          try{ const res = await api.upload(fileRef.current.files[0]); toast.success('Uploaded'); onUploaded && onUploaded(res.data) }
          catch(e){ toast.error('Upload failed') }
          finally{ setLoading(false) }
        }} className="btn btn-ghost btn-sm">Upload</button>
        {loading && <span className="ml-2 text-sm text-muted">Uploading...</span>}
      </div>
    </div>
  )
}
