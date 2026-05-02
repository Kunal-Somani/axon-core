const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export const API_HTTP = API_BASE
export const API_WS = API_BASE.replace(/^http/, 'ws')
export const ENDPOINTS = {
  health:     `${API_HTTP}/health`,
  ingest:     `${API_HTTP}/ingest`,
  history:    (sessionId: string) => `${API_HTTP}/sessions/${sessionId}/history`,
  transcribe: `${API_HTTP}/audio/transcribe`,
  synthesize: `${API_HTTP}/audio/synthesize`,
  wsChat:     `${API_WS}/ws/chat`,
} as const
