'use client'
import { useEffect, useRef, useCallback } from 'react'
import { useAxonStore, Route } from '../store'

const WS_URL = 'ws://localhost:8000/ws/chat'

export function useAxonWebSocket() {
  const ws = useRef<WebSocket | null>(null)
  const { sessionId, addMessage, appendToken, finalizeMessage, setWsStatus, setStreaming } = useAxonStore()

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return
    setWsStatus('connecting')
    const socket = new WebSocket(WS_URL)
    ws.current = socket

    socket.onopen = () => setWsStatus('connected')
    socket.onclose = () => {
      setWsStatus('disconnected')
      setTimeout(connect, 3000)
    }
    socket.onerror = () => setWsStatus('disconnected')

    let currentMsgId: string | null = null

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'token') {
        if (!currentMsgId) {
          currentMsgId = addMessage({ role: 'assistant', content: '', route: 'pending', isStreaming: true })
        }
        appendToken(currentMsgId, data.data)
      } else if (data.type === 'done') {
        if (currentMsgId) {
          finalizeMessage(currentMsgId, {
            route: data.route as Route,
            confidence: data.confidence,
            sources: data.sources || []
          })
          currentMsgId = null
        }
        setStreaming(false)
      } else if (data.type === 'error') {
        if (currentMsgId) {
          finalizeMessage(currentMsgId, { route: 'general_conversation', confidence: 0, sources: [] })
          currentMsgId = null
        }
        setStreaming(false)
      }
    }
  }, [sessionId])

  useEffect(() => {
    connect()
    return () => ws.current?.close()
  }, [connect])

  const sendMessage = useCallback((query: string, imageBase64?: string) => {
    if (ws.current?.readyState !== WebSocket.OPEN) return false
    addMessage({ role: 'user', content: query })
    setStreaming(true)
    ws.current.send(JSON.stringify({ query, session_id: sessionId, image_base64: imageBase64 }))
    return true
  }, [sessionId])

  return { sendMessage }
}
