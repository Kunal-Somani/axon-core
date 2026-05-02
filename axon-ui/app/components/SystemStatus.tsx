'use client'
import { useEffect } from 'react'
import { useAxonStore } from '../store'
import { Wifi, WifiOff, Database, Cpu } from 'lucide-react'
import { ENDPOINTS } from '../../lib/config'

export function SystemStatus() {
  const { health, setHealth, wsStatus } = useAxonStore()

  useEffect(() => {
    const poll = () =>
      fetch(ENDPOINTS.health)
        .then(r => r.json())
        .then(setHealth)
        .catch(() => {})
    poll()
    const id = setInterval(poll, 10000)
    return () => clearInterval(id)
  }, [])

  const dot = (ok: boolean) => (
    <span style={{ width: 6, height: 6, borderRadius: '50%', background: ok ? 'var(--success)' : 'var(--danger)', display: 'inline-block', marginRight: 5 }} />
  )

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 11, color: 'var(--text-muted)' }}>
      <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
        {wsStatus === 'connected' ? <Wifi size={12} color="var(--success)" /> : <WifiOff size={12} color="var(--danger)" />}
        {wsStatus}
      </span>
      {health && (
        <>
          <span>{dot(health.models.llm.loaded)}LLM</span>
          <span>{dot(health.models.router.loaded)}Router</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Database size={11} />{health.qdrant.document_count} docs
          </span>
          <span style={{ color: 'var(--text-muted)' }}>up {Math.round(health.uptime_seconds / 60)}m</span>
        </>
      )}
    </div>
  )
}
