'use client'
import { useCallback, useRef } from 'react'
import { ENDPOINTS } from '../../lib/config'

export function useTextToSpeech() {
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const speak = useCallback(async (text: string) => {
    try {
      const res = await fetch(ENDPOINTS.synthesize, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      })
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      if (audioRef.current) {
        audioRef.current.pause()
        URL.revokeObjectURL(audioRef.current.src)
      }
      audioRef.current = new Audio(url)
      audioRef.current.play()
    } catch {
      console.error('TTS failed')
    }
  }, [])

  const stop = useCallback(() => {
    audioRef.current?.pause()
  }, [])

  return { speak, stop }
}
