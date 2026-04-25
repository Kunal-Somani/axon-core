'use client'
import { Route } from '../store'
import { Brain, Wrench, MessageCircle, FileText, Image, Loader2 } from 'lucide-react'

const ROUTE_CONFIG: Record<Route, { label: string; color: string; bg: string; Icon: any }> = {
  personal_knowledge_query: { label: 'Knowledge Base', color: '#60a5fa', bg: 'rgba(37,99,235,0.15)', Icon: Brain },
  document_analysis:        { label: 'Document Analysis', color: '#a78bfa', bg: 'rgba(124,58,237,0.15)', Icon: FileText },
  system_tool_execution:    { label: 'System Tool', color: '#34d399', bg: 'rgba(16,185,129,0.15)', Icon: Wrench },
  general_conversation:     { label: 'General AI', color: '#f9a8d4', bg: 'rgba(236,72,153,0.15)', Icon: MessageCircle },
  image_analysis:           { label: 'Vision', color: '#fbbf24', bg: 'rgba(245,158,11,0.15)', Icon: Image },
  pending:                  { label: 'Processing', color: '#a1a1aa', bg: 'rgba(63,63,70,0.3)', Icon: Loader2 },
}

export function RoutingBadge({ route, confidence }: { route: Route; confidence?: number }) {
  const cfg = ROUTE_CONFIG[route] || ROUTE_CONFIG.pending
  const { label, color, bg, Icon } = cfg
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: bg, border: `1px solid ${color}30`, borderRadius: 6, padding: '2px 8px', marginBottom: 8 }}>
      <Icon size={11} color={color} style={route === 'pending' ? { animation: 'spin 1s linear infinite' } : {}} />
      <span style={{ color, fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</span>
      {confidence !== undefined && (
        <span style={{ color, fontSize: 10, opacity: 0.7 }}>{Math.round(confidence * 100)}%</span>
      )}
    </div>
  )
}
