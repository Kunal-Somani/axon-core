import { create } from 'zustand'

export type Route = 'personal_knowledge_query' | 'system_tool_execution' | 'general_conversation' | 'document_analysis' | 'image_analysis' | 'pending'

export interface Source { source: string; score: number }
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  route?: Route
  confidence?: number
  sources?: Source[]
  isStreaming?: boolean
  timestamp: Date
}

export interface ModelStatus {
  loaded: boolean
  load_time_ms?: number
  model_exists?: boolean
}

export interface HealthData {
  status: string
  uptime_seconds: number
  models: { embedder: ModelStatus; llm: ModelStatus; router: ModelStatus; vision: ModelStatus }
  qdrant: { document_count: number; status: string }
  available_tools: string[]
}

interface AxonStore {
  messages: Message[]
  sessionId: string
  wsStatus: 'connecting' | 'connected' | 'disconnected'
  health: HealthData | null
  isStreaming: boolean
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => string
  appendToken: (id: string, token: string) => void
  finalizeMessage: (id: string, data: { route: Route; confidence: number; sources: Source[] }) => void
  setWsStatus: (s: AxonStore['wsStatus']) => void
  setHealth: (h: HealthData) => void
  setStreaming: (v: boolean) => void
}

let msgCounter = 0

export const useAxonStore = create<AxonStore>((set) => ({
  messages: [],
  sessionId: typeof window !== 'undefined' ? (localStorage.getItem('axon_session') || crypto.randomUUID()) : crypto.randomUUID(),
  wsStatus: 'disconnected',
  health: null,
  isStreaming: false,
  addMessage: (msg) => {
    const id = `msg_${Date.now()}_${msgCounter++}`
    set(s => ({ messages: [...s.messages, { ...msg, id, timestamp: new Date() }] }))
    return id
  },
  appendToken: (id, token) => set(s => ({
    messages: s.messages.map(m => m.id === id ? { ...m, content: m.content + token } : m)
  })),
  finalizeMessage: (id, data) => set(s => ({
    messages: s.messages.map(m => m.id === id ? { ...m, ...data, isStreaming: false } : m)
  })),
  setWsStatus: (wsStatus) => set({ wsStatus }),
  setHealth: (health) => set({ health }),
  setStreaming: (isStreaming) => set({ isStreaming }),
}))
