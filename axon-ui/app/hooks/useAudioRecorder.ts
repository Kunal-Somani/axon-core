'use client'
import { useState, useRef, useCallback } from 'react'
import { ENDPOINTS } from '../../lib/config'

type RecordingState = 'idle' | 'recording' | 'transcribing' | 'error'

export function useAudioRecorder(onTranscript: (text: string) => void) {
  const [state, setState] = useState<RecordingState>('idle')
  const [error, setError] = useState<string>('')
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const chunks = useRef<BlobPart[]>([])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      chunks.current = []
      recorder.ondataavailable = (e) => chunks.current.push(e.data)
      recorder.onstop = async () => {
        setState('transcribing')
        try {
          const blob = new Blob(chunks.current, { type: 'audio/webm' })
          const form = new FormData()
          form.append('file', blob, 'recording.webm')
          const res = await fetch(ENDPOINTS.transcribe, { method: 'POST', body: form })
          const data = await res.json()
          onTranscript(data.transcript ?? '')
          setState('idle')
        } catch {
          setState('error')
          setError('Transcription failed')
        }
        stream.getTracks().forEach(t => t.stop())
      }
      recorder.start()
      mediaRecorder.current = recorder
      setState('recording')
    } catch (e) {
      setState('error')
      setError('Microphone access denied')
    }
  }, [onTranscript])

  const stopRecording = useCallback(() => {
    mediaRecorder.current?.stop()
  }, [])

  return { state, error, startRecording, stopRecording }
}
