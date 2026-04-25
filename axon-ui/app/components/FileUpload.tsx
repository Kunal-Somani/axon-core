'use client'
import { useRef, useState } from 'react'
import { Upload, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

type Status = 'idle' | 'uploading' | 'success' | 'error'

export function FileUpload() {
  const [status, setStatus] = useState<Status>('idle')
  const [message, setMessage] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    setStatus('uploading')
    setMessage(`Ingesting ${file.name}...`)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('http://localhost:8000/ingest', { method: 'POST', body: form })
      const data = await res.json()
      if (res.ok) {
        setStatus('success')
        setMessage(`✓ ${data.filename}: ${data.ingested} new chunks`)
      } else {
        setStatus('error')
        setMessage(data.detail || 'Upload failed')
      }
    } catch (e) {
      setStatus('error')
      setMessage('Backend unreachable')
    }
    setTimeout(() => { setStatus('idle'); setMessage('') }, 4000)
  }

  return (
    <div>
      <input ref={inputRef} type="file" accept=".pdf,.txt,.png,.jpg,.jpeg" style={{ display: 'none' }}
        onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])} />
      <button onClick={() => inputRef.current?.click()} style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8,
        padding: '8px 12px', color: 'var(--text-secondary)', cursor: 'pointer',
        display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, transition: 'all 0.2s'
      }}>
        {status === 'uploading' && <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />}
        {status === 'success' && <CheckCircle size={14} color="var(--success)" />}
        {status === 'error' && <AlertCircle size={14} color="var(--danger)" />}
        {status === 'idle' && <Upload size={14} />}
        {status === 'idle' ? 'Upload Document' : message}
      </button>
    </div>
  )
}
