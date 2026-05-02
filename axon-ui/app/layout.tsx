import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Axon — Self-Hosted Multimodal AI',
  description: 'Hybrid RAG, semantic routing, vision, and speech. Zero external LLM APIs.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  )
}
