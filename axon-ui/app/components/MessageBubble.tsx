'use client'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message } from '../store'
import { RoutingBadge } from './RoutingBadge'
import { User, Bot } from 'lucide-react'

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 20 }}>
      <div style={{ maxWidth: '78%', display: 'flex', gap: 12, flexDirection: isUser ? 'row-reverse' : 'row', alignItems: 'flex-start' }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: isUser ? 'var(--accent)' : 'rgba(37,99,235,0.15)',
          border: isUser ? 'none' : '1px solid rgba(37,99,235,0.3)'
        }}>
          {isUser ? <User size={16} /> : <Bot size={16} color="#60a5fa" />}
        </div>
        <div style={{
          background: isUser ? 'var(--accent)' : 'var(--bg-card)',
          border: isUser ? 'none' : '1px solid var(--border)',
          borderRadius: isUser ? '18px 4px 18px 18px' : '4px 18px 18px 18px',
          padding: '12px 16px',
        }}>
          {!isUser && message.route && (
            <RoutingBadge route={message.route} confidence={message.confidence} />
          )}
          <div style={{ fontSize: 14, lineHeight: 1.65, color: isUser ? '#fff' : 'var(--text-primary)' }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content || (message.isStreaming ? '▌' : '')}</ReactMarkdown>
          </div>
          {!isUser && message.sources && message.sources.length > 0 && (
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border)' }}>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Sources</p>
              {message.sources.map((s, i) => (
                <div key={i} style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                  <span>📄 {s.source}</span>
                  <span style={{ color: 'var(--accent)' }}>{(s.score * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
