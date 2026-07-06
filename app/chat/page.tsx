import ChatClient from './ChatClient'
import Link from 'next/link'

export const metadata = { title: 'Research Wiki — Chat' }

export default function ChatPage() {
  return (
    <div className="flex flex-col h-screen">
      <header className="flex items-center gap-4 px-6 py-4 border-b border-neutral-800 shrink-0">
        <Link href="/" className="text-xs text-neutral-600 hover:text-neutral-400 transition-colors">
          ← Research Wiki
        </Link>
        <h1 className="text-sm font-medium text-white">RAG Chat</h1>
        <p className="text-xs text-neutral-600 hidden sm:block">
          기관 리서치 지식베이스 기반 Q&amp;A — 시점 명시 + 하우스별 뷰 비교
        </p>
      </header>
      <div className="flex-1 overflow-hidden">
        <ChatClient />
      </div>
    </div>
  )
}
