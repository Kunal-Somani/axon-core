'use client'
import { useRef, useState, useEffect, useCallback } from 'react'
import { useAxonStore } from './store'
import { useAxonWebSocket } from './hooks/useAxonWebSocket'
import { MessageBubble } from './components/MessageBubble'
import { SystemStatus } from './components/SystemStatus'
import { FileUpload } from './components/FileUpload'
import { Send, Zap, ImagePlus } from 'lucide-react'

export default function Home() {
  const [input, setInput] = useState('')
  const [pendingImage, setPendingImage] = useState<string | null>(null)
  const { messages, isStreaming } = useAxonStore()
  const { sendMessage } = useAxonWebSocket()
  const scrollRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg-primary)' }}>
      {/* Header */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 24px', borderBottom: '1px solid var(--border)',
        background: 'rgba(24,24,27,0.8)', backdropFilter: 'blur(12px)', position: 'sticky', top: 0, zIndex: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: 'linear-gradient(135deg,#2563eb,#7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Zap size={18} color="white" />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 15, fontWeight: 700, letterSpacing: '-0.02em' }}>Axon</h1>
            <p style={{ margin: 0, fontSize: 11, color: 'var(--text-muted)' }}>Hybrid RAG · Multimodal · Local</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <FileUpload />
          <SystemStatus />
        </div>
      </header>

      {/* Messages */}
      <main style={{ flex: 1, overflowY: 'auto', padding: '24px', maxWidth: 860, width: '100%', margin: '0 auto' }} className="scrollbar-thin">
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', marginTop: 100 }}>
            <div style={{ width: 64, height: 64, borderRadius: 16, background: 'linear-gradient(135deg,#2563eb22,#7c3aed22)', border: '1px solid #2563eb33', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
              <Zap size={28} color="#60a5fa" />
            </div>
            <h2 style={{ color: 'var(--text-primary)', fontSize: 22, fontWeight: 700, margin: '0 0 8px' }}>Axon is ready</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Ask about your documents, run tools, or just chat.</p>
          </div>
        )}
        {messages.map(msg => <MessageBubble key={msg.id} message={msg} />)}
        <div ref={scrollRef} />
      </main>

      {/* Input */}
      <div style={{ padding: '16px 24px 24px', borderTop: '1px solid var(--border)', background: 'var(--bg-secondary)' }}>
        <div style={{ maxWidth: 860, margin: '0 auto' }}>
          {pendingImage && (
            <div style={{ marginBottom: 8, padding: '6px 12px', background: 'rgba(37,99,235,0.15)', borderRadius: 8, fontSize: 12, color: '#60a5fa', display: 'flex', justifyContent: 'space-between' }}>
              <span>🖼 Image attached</span>
              <button onClick={() => setPendingImage(null)} style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', fontSize: 12 }}>Remove</button>
            </div>
          )}
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            <input type="file" ref={fileInputRef} accept="image/*" style={{ display: 'none' }} onChange={handleImageFile} />
            <button onClick={() => fileInputRef.current?.click()} style={{
              background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10,
              padding: '12px', color: 'var(--text-muted)', cursor: 'pointer', flexShrink: 0
            }}>
              <ImagePlus size={18} />
            </button>
            <textarea
              style={{
                flex: 1, background: 'var(--bg-card)', border: '1px solid var(--border)',
                borderRadius: 12, padding: '12px 16px', fontSize: 14, color: 'var(--text-primary)',
                resize: 'none', outline: 'none', fontFamily: 'inherit', lineHeight: 1.5, minHeight: 48, maxHeight: 160
              }}
              placeholder="Message Axon... (Shift+Enter for newline, paste an image)"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              rows={1}
            />
            <button onClick={handleSend} disabled={isStreaming || !input.trim()} style={{
              background: isStreaming || !input.trim() ? 'var(--bg-card)' : 'var(--accent)',
              border: '1px solid var(--border)', borderRadius: 10, padding: '12px 16px',
              color: isStreaming || !input.trim() ? 'var(--text-muted)' : 'white',
              cursor: isStreaming || !input.trim() ? 'not-allowed' : 'pointer', flexShrink: 0, transition: 'all 0.2s'
            }}>
              <Send size={18} />
            </button>
          </div>
          <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--text-muted)', marginTop: 10 }}>
            Hybrid RRF · BART Router · Phi-3 Local LLM · BLIP Vision · BM25+Dense
          </p>
        </div>
      </div>
    </div>
  )
}