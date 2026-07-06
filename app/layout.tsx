import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import './globals.css'
import EmbeddedChrome from '@/components/EmbeddedChrome'

// Session 0 스켈레톤 레이아웃. 도메인 네비게이션(Header)·챗 팝업은 폐기됨 —
// /wiki·/chat·/review·/scoreboard UI 는 Phase 3~4 에서 재구축한다.
const geistSans = Geist({ variable: '--font-geist-sans', subsets: ['latin'] })
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Research Wiki',
  description: '글로벌 기관 리서치 수집·지식화·wiki/RAG 개인 도구',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-neutral-950 text-neutral-100 min-h-screen`}>
        <EmbeddedChrome />
        <main>{children}</main>
      </body>
    </html>
  )
}
