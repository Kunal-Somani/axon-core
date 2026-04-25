import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Axon — Multimodal AI Assistant',
  description: 'Local multimodal AI with hybrid RAG, semantic routing, and vision',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  )
}
