'use client'

import { useState, useRef, useEffect, useCallback } from 'react'

type Source = { title: string; url: string; issuer: string | null; published_at: string | null }
type Message = { role: 'user' | 'assistant'; content: string; sources?: Source[] }

const SUGGESTIONS = [
  '전력기기 섹터 기관별 최신 뷰를 비교해줘',
  'HBM 수요 전망 변화 추이를 알려줘',
  'AI 반도체 섹터에서 상충하는 뷰가 있는 논점은?',
  'IMF와 Goldman Sachs의 에너지 인프라 전망은?',
]

export default function ChatClient() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const [mode, setMode] = useState<'normal' | 'historical'>('normal')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const submit = useCallback(async (text: string) => {
    if (!text.trim() || loading) return

    const userMsg: Message = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    // assistant 플레이스홀더
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }])

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId, mode }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let sources: Source[] | undefined

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const ev = JSON.parse(line.slice(6))
            if (ev.type === 'session' && ev.session_id) {
              setSessionId(ev.session_id)
            } else if (ev.type === 'text') {
              setMessages((prev) => {
                const copy = [...prev]
                const last = { ...copy[copy.length - 1] }
                last.content += ev.content
                copy[copy.length - 1] = last
                return copy
              })
            } else if (ev.type === 'sources') {
              sources = ev.sources
            } else if (ev.type === 'done') {
              if (sources?.length) {
                setMessages((prev) => {
                  const copy = [...prev]
                  copy[copy.length - 1] = { ...copy[copy.length - 1], sources }
                  return copy
                })
              }
            }
          } catch {}
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const copy = [...prev]
        copy[copy.length - 1] = {
          role: 'assistant',
          content: `오류가 발생했습니다: ${err instanceof Error ? err.message : String(err)}`,
        }
        return copy
      })
    } finally {
      setLoading(false)
    }
  }, [loading, sessionId, mode])

  const reset = () => {
    setMessages([])
    setSessionId(undefined)
  }

  return (
    <div className="flex flex-col h-full">
      {/* 툴바 */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-neutral-800">
        <span className="text-xs text-neutral-500">모드:</span>
        <button
          onClick={() => setMode('normal')}
          className={`text-xs px-3 py-1 rounded-full transition-colors ${
            mode === 'normal'
              ? 'bg-blue-900/50 text-blue-300 border border-blue-700'
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          최신 우선
        </button>
        <button
          onClick={() => setMode('historical')}
          className={`text-xs px-3 py-1 rounded-full transition-colors ${
            mode === 'historical'
              ? 'bg-amber-900/50 text-amber-300 border border-amber-700'
              : 'text-neutral-500 hover:text-neutral-300'
          }`}
        >
          과거 뷰 조회
        </button>
        {messages.length > 0 && (
          <button
            onClick={reset}
            className="ml-auto text-xs text-neutral-600 hover:text-neutral-400 transition-colors"
          >
            대화 초기화
          </button>
        )}
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {messages.length === 0 ? (
          <div className="py-12">
            <p className="text-sm text-neutral-500 mb-6 text-center">
              글로벌 기관 리서치를 질문하세요
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => submit(s)}
                  className="text-left text-xs text-neutral-400 bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-3 hover:border-neutral-600 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* 입력창 */}
      <div className="px-6 py-4 border-t border-neutral-800">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            submit(input)
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="질문을 입력하세요..."
            disabled={loading}
            className="flex-1 bg-neutral-900 border border-neutral-700 text-sm text-white rounded-lg px-4 py-2.5 placeholder:text-neutral-600 focus:outline-none focus:border-neutral-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="text-sm px-4 py-2.5 bg-blue-700 hover:bg-blue-600 text-white rounded-lg disabled:opacity-40 transition-colors"
          >
            전송
          </button>
        </form>
      </div>
    </div>
  )
}

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] ${isUser ? 'order-2' : 'order-1'}`}>
        {isUser ? (
          <div className="bg-blue-800/40 border border-blue-700/40 rounded-2xl rounded-tr-sm px-4 py-3">
            <p className="text-sm text-neutral-200">{msg.content}</p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="bg-neutral-900 border border-neutral-800 rounded-2xl rounded-tl-sm px-4 py-3">
              <p className="text-sm text-neutral-200 whitespace-pre-wrap leading-relaxed">
                {msg.content || <span className="text-neutral-600 animate-pulse">▌</span>}
              </p>
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="flex flex-wrap gap-1.5 px-1">
                {msg.sources.map((s, i) => (
                  <a
                    key={i}
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-neutral-500 bg-neutral-900 border border-neutral-800 rounded-full px-2.5 py-1 hover:border-neutral-600 hover:text-neutral-300 transition-colors truncate max-w-48"
                  >
                    {s.issuer ?? s.title} {s.published_at ? s.published_at.slice(0, 7) : ''}
                  </a>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
