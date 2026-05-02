'use client'
import { useRef, useState, useEffect, useCallback } from 'react'
import { useAxonStore } from './store'
import { useAxonWebSocket } from './hooks/useAxonWebSocket'
import { useAudioRecorder } from './hooks/useAudioRecorder'
import { useTextToSpeech } from './hooks/useTextToSpeech'
import { FileUpload } from './components/FileUpload'
import { Send, ImagePlus, Mic, MicOff, Volume2, VolumeX, Loader2, Copy, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

export default function Home() {
  const [input, setInput] = useState('')
  const [pendingImage, setPendingImage] = useState<string | null>(null)
  const [ttsEnabled, setTtsEnabled] = useState(false)
  const [copiedId, setCopiedId] = useState(false)
  
  const { messages, isStreaming, health, wsStatus, sessionId } = useAxonStore()
  const { sendMessage } = useAxonWebSocket()
  const { speak } = useTextToSpeech()
  const scrollRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { state: recordingState, error: recordingError, startRecording, stopRecording } = useAudioRecorder((transcript) => {
    setInput(transcript)
  })

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!isStreaming && ttsEnabled && messages.length > 0) {
      const lastMsg = messages[messages.length - 1]
      if (lastMsg.role === 'assistant' && lastMsg.content) {
        speak(lastMsg.content)
      }
    }
  }, [isStreaming, ttsEnabled, messages, speak])

  // Initial health fetch
  useEffect(() => {
    const poll = () =>
      fetch(process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/health` : 'http://localhost:8000/health')
        .then(r => r.json())
        .then(useAxonStore.getState().setHealth)
        .catch(() => {})
    poll()
    const id = setInterval(poll, 10000)
    return () => clearInterval(id)
  }, [])

  const handleSend = useCallback(() => {
    const q = input.trim()
    if (!q || isStreaming) return
    sendMessage(q, pendingImage || undefined)
    setInput('')
    setPendingImage(null)
  }, [input, isStreaming, pendingImage, sendMessage])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const handlePaste = async (e: React.ClipboardEvent) => {
    const item = Array.from(e.clipboardData.items).find(i => i.type.startsWith('image/'))
    if (!item) return
    const blob = item.getAsFile()
    if (!blob) return
    const reader = new FileReader()
    reader.onload = () => { if (typeof reader.result === 'string') setPendingImage(reader.result.split(',')[1]) }
    reader.readAsDataURL(blob)
  }

  const handleImageFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => { if (typeof reader.result === 'string') setPendingImage(reader.result.split(',')[1]) }
    reader.readAsDataURL(file)
  }

  const copySessionId = () => {
    navigator.clipboard.writeText(sessionId)
    setCopiedId(true)
    setTimeout(() => setCopiedId(false), 2000)
  }

  const lastAssistantMsg = [...messages].reverse().find(m => m.role === 'assistant')

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--void)' }}>
      {/* LEFT PANEL */}
      <aside style={{ width: 220, background: 'var(--surface-0)', borderRight: '1px solid var(--border-dim)', display: 'flex', flexDirection: 'column', padding: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 32 }}>
          <h1 className="mono" style={{ margin: 0, fontSize: 20, fontWeight: 600, color: 'var(--text-0)', letterSpacing: '0.05em' }}>AXON</h1>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: wsStatus === 'connected' ? 'var(--success)' : 'var(--danger)', boxShadow: wsStatus === 'connected' ? '0 0 8px var(--success)' : 'none' }} />
        </div>

        <div style={{ flex: 1 }}>
          <h3 className="mono" style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 12, letterSpacing: '0.05em' }}>MODELS</h3>
          {health ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
              {Object.entries(health.models).map(([name, status]) => (
                <div key={name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: status.loaded ? 'var(--text-0)' : 'var(--text-2)' }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: status.loaded ? 'var(--success)' : 'var(--border-dim)' }} />
                    <span style={{ textTransform: 'capitalize' }}>{name}</span>
                  </div>
                  {status.load_time_ms && <span className="mono" style={{ color: 'var(--text-2)' }}>{status.load_time_ms}ms</span>}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: 12, color: 'var(--text-2)' }}>Loading status...</div>
          )}

          <div style={{ margin: '32px 0', borderTop: '1px solid var(--border-dim)', paddingTop: 32 }}>
            <h3 className="mono" style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 12, letterSpacing: '0.05em' }}>DATABASE</h3>
            <div style={{ fontSize: 12, color: 'var(--text-1)' }}>
              {health?.qdrant.document_count ?? 0} docs indexed
            </div>
          </div>

          <div style={{ marginBottom: 32 }}>
             <FileUpload />
          </div>
        </div>

        <div style={{ borderTop: '1px solid var(--border-dim)', paddingTop: 16 }}>
           <h3 className="mono" style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 8, letterSpacing: '0.05em' }}>SESSION</h3>
           <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--surface-1)', padding: '6px 10px', borderRadius: 4, border: '1px solid var(--border-dim)' }}>
              <span className="mono" style={{ fontSize: 11, color: 'var(--text-1)', overflow: 'hidden', textOverflow: 'ellipsis' }}>{sessionId.slice(0, 12)}...</span>
              <button onClick={copySessionId} style={{ background: 'none', border: 'none', color: 'var(--text-2)', cursor: 'pointer' }}>
                {copiedId ? <Check size={14} color="var(--success)" /> : <Copy size={14} />}
              </button>
           </div>
        </div>
      </aside>

      {/* CENTER PANEL */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--void)' }}>
        <header style={{ padding: '16px 24px', borderBottom: '1px solid var(--border-dim)', display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={() => setTtsEnabled(!ttsEnabled)} style={{
            background: 'none', border: 'none', color: ttsEnabled ? 'var(--text-0)' : 'var(--text-2)',
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, transition: 'all 0.2s', padding: 0, fontSize: 12
          }} title="Toggle Text-to-Speech">
            {ttsEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
            <span className="mono">TTS</span>
          </button>
        </header>

        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 10%', display: 'flex', flexDirection: 'column', gap: 24 }} className="scrollbar-thin">
          {messages.map(msg => (
            <div key={msg.id} style={{
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%',
              background: msg.role === 'user' ? 'var(--accent-muted)' : 'var(--surface-1)',
              border: `1px solid ${msg.role === 'user' ? 'var(--accent-glow)' : 'var(--border-dim)'}`,
              padding: '16px 20px', borderRadius: 8,
              color: 'var(--text-0)'
            }}>
              {msg.role === 'user' ? (
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
              ) : (
                <div className="prose prose-invert" style={{ fontSize: 14 }}>
                  <ReactMarkdown
                    components={{
                      code({ node, inline, className, children, ...props }: any) {
                        return inline ? (
                          <code className="mono" style={{ background: 'var(--surface-2)', padding: '2px 4px', borderRadius: 4, fontSize: '0.9em' }} {...props}>{children}</code>
                        ) : (
                          <pre style={{ background: 'var(--surface-0)', padding: 12, borderRadius: 6, overflowX: 'auto', border: '1px solid var(--border-dim)', marginTop: 8, marginBottom: 8 }}>
                            <code className="mono" style={{ fontSize: 13 }} {...props}>{children}</code>
                          </pre>
                        )
                      }
                    }}
                  >{msg.content}</ReactMarkdown>
                  {msg.isStreaming && <span className="cursor-blink mono" style={{ display: 'inline-block', width: 8, height: 16, background: 'var(--accent)', marginLeft: 4, verticalAlign: 'middle' }} />}
                </div>
              )}
            </div>
          ))}
          <div ref={scrollRef} />
        </div>

        <div style={{ padding: '20px 10%', background: 'var(--surface-2)', borderTop: '1px solid var(--border-dim)' }}>
           {pendingImage && (
             <div style={{ marginBottom: 12, padding: '6px 12px', background: 'var(--surface-1)', border: '1px solid var(--border-dim)', borderRadius: 4, fontSize: 12, color: 'var(--text-1)', display: 'flex', justifyContent: 'space-between' }}>
               <span>🖼 Image attached</span>
               <button onClick={() => setPendingImage(null)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', fontSize: 12 }}>Remove</button>
             </div>
           )}
           {recordingState !== 'idle' && (
             <div className="mono" style={{ marginBottom: 12, fontSize: 11, color: recordingState === 'error' ? 'var(--danger)' : 'var(--accent)' }}>
               {recordingState === 'recording' && "RECORDING_AUDIO... [MIC_ACTIVE]"}
               {recordingState === 'transcribing' && "TRANSCRIBING... [AWAITING_BACKEND]"}
               {recordingState === 'error' && `ERR_AUDIO: ${recordingError}`}
             </div>
           )}
           
           <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
             <input type="file" ref={fileInputRef} accept="image/*" style={{ display: 'none' }} onChange={handleImageFile} />
             <button onClick={() => fileInputRef.current?.click()} style={{
               background: 'var(--surface-0)', border: '1px solid var(--border-dim)', borderRadius: 6,
               padding: '12px', color: 'var(--text-1)', cursor: 'pointer', flexShrink: 0
             }} title="Attach Image">
               <ImagePlus size={18} />
             </button>

             <button 
               onClick={recordingState === 'recording' ? stopRecording : startRecording}
               disabled={recordingState === 'transcribing'}
               style={{
                 background: recordingState === 'recording' ? 'rgba(248,113,113,0.1)' : 'var(--surface-0)', 
                 border: '1px solid ' + (recordingState === 'recording' ? 'var(--danger)' : 'var(--border-dim)'), 
                 borderRadius: 6, padding: '12px', flexShrink: 0,
                 color: recordingState === 'recording' ? 'var(--danger)' : 'var(--text-1)', 
                 cursor: recordingState === 'transcribing' ? 'not-allowed' : 'pointer',
               }}
               title="Voice Input"
             >
               {recordingState === 'transcribing' ? <Loader2 size={18} className="cursor-blink" /> :
                recordingState === 'recording' ? <MicOff size={18} /> : <Mic size={18} />}
             </button>

             <textarea
               style={{
                 flex: 1, background: 'var(--surface-0)', border: '1px solid var(--border-dim)',
                 borderRadius: 6, padding: '14px 16px', fontSize: 14, color: 'var(--text-0)',
                 resize: 'none', outline: 'none', fontFamily: 'inherit', lineHeight: 1.5, minHeight: 50, maxHeight: 200
               }}
               placeholder="> Input prompt... (Shift+Enter for newline)"
               value={input}
               onChange={e => setInput(e.target.value)}
               onKeyDown={handleKeyDown}
               onPaste={handlePaste}
               rows={1}
             />
             
             <button onClick={handleSend} disabled={isStreaming || !input.trim()} style={{
               background: isStreaming || !input.trim() ? 'var(--surface-0)' : 'var(--accent)',
               border: '1px solid ' + (isStreaming || !input.trim() ? 'var(--border-dim)' : 'transparent'), 
               borderRadius: 6, padding: '12px 20px',
               color: isStreaming || !input.trim() ? 'var(--text-2)' : '#fff',
               cursor: isStreaming || !input.trim() ? 'not-allowed' : 'pointer', flexShrink: 0
             }}>
               <Send size={18} />
             </button>
           </div>
        </div>
      </main>

      {/* RIGHT PANEL */}
      <aside className="hidden lg:flex" style={{ width: 260, background: 'var(--surface-0)', borderLeft: '1px solid var(--border-dim)', flexDirection: 'column', padding: 20, overflowY: 'auto' }}>
        <h3 className="mono" style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 16, letterSpacing: '0.05em' }}>ROUTING INSPECTOR</h3>
        {lastAssistantMsg ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 12 }}>
                <span style={{ color: 'var(--text-1)' }}>Primary Route</span>
                <span className="mono" style={{ color: 'var(--accent)' }}>{lastAssistantMsg.route || 'N/A'}</span>
              </div>
              <div style={{ height: 4, background: 'var(--surface-1)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{ height: '100%', background: 'var(--accent)', width: `${(lastAssistantMsg.confidence || 0) * 100}%` }} />
              </div>
            </div>
            
            {lastAssistantMsg.all_scores && (
              <div>
                <span style={{ fontSize: 11, color: 'var(--text-2)', display: 'block', marginBottom: 8 }}>All Scores</span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {Object.entries(lastAssistantMsg.all_scores).map(([route, score]) => (
                    <div key={route} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                       <span className="mono" style={{ fontSize: 10, color: 'var(--text-1)', width: 100, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{route}</span>
                       <div style={{ flex: 1, height: 2, background: 'var(--surface-1)' }}>
                         <div style={{ height: '100%', background: 'var(--text-2)', width: `${score * 100}%` }} />
                       </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {lastAssistantMsg.sources && lastAssistantMsg.sources.length > 0 && (
              <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border-dim)' }}>
                <h3 className="mono" style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 12, letterSpacing: '0.05em' }}>SOURCES</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {lastAssistantMsg.sources.map((s, i) => (
                    <div key={i} style={{ background: 'var(--surface-1)', border: '1px solid var(--border-dim)', padding: '8px 10px', borderRadius: 4 }}>
                      <div className="mono" style={{ fontSize: 10, color: 'var(--accent)', marginBottom: 4 }}>Score: {s.score.toFixed(3)}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-0)', wordBreak: 'break-all' }}>{s.source.split('/').pop()}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ fontSize: 12, color: 'var(--text-2)' }}>No message selected.</div>
        )}
      </aside>
    </div>
  )
}