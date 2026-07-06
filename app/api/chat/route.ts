import { NextRequest } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { auth } from '@/auth'
import { db } from '@/lib/db'
import { chat_sessions, chat_messages } from '@/db/schema'
import { eq, asc } from 'drizzle-orm'
import {
  embedQuery,
  detectIntent,
  searchKnowledge,
  buildComparisonContext,
  buildViewChangeContext,
  buildOutcomeContext,
  formatSearchContext,
} from '@/lib/rag'

export const runtime = 'nodejs'
export const maxDuration = 60

const anthropic = new Anthropic()

const SYSTEM_BASE = `당신은 글로벌 기관 리서치 전문 애널리스트 AI입니다.
아래 [지식베이스] 컨텍스트를 기반으로 답변하세요.

필수 규칙:
1. 시점 명시 필수 — 예: "Goldman Sachs는 2026년 1월 기준으로 ~라고 전망했습니다"
2. 현재형 단정 금지 — "~입니다" 대신 "~전망했습니다", "~분석한 바 있습니다"
3. 발행처 + 발행 시점을 항상 함께 인용
4. 지식베이스에 없는 내용 — "현재 수집된 리서치에 해당 정보가 없습니다"
5. 상충하는 뷰가 있으면 양쪽을 모두 공정하게 제시`

function enc(obj: unknown) {
  return `data: ${JSON.stringify(obj)}\n\n`
}

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session) return new Response('Unauthorized', { status: 401 })

  const { message, session_id, mode = 'normal' } = await req.json() as {
    message: string
    session_id?: string
    mode?: 'normal' | 'historical'
  }

  if (!message?.trim()) return new Response('Bad Request', { status: 400 })

  // ── 세션 관리 ───────────────────────────────────────────────────────────────
  let sid = session_id
  if (!sid) {
    const [newSession] = await db
      .insert(chat_sessions)
      .values({ mode })
      .returning({ id: chat_sessions.id })
    sid = newSession.id
  }

  // 대화 히스토리 (최근 20개)
  const history = await db
    .select({ role: chat_messages.role, content: chat_messages.content })
    .from(chat_messages)
    .where(eq(chat_messages.session_id, sid))
    .orderBy(asc(chat_messages.created_at))
    .limit(20)

  // 유저 메시지 저장
  await db.insert(chat_messages).values({
    session_id: sid,
    role: 'user',
    content: message,
  })

  // ── 질의 의도 감지 + 컨텍스트 빌드 ─────────────────────────────────────────
  const intent = detectIntent(message)
  const historical = mode === 'historical' || intent === 'historical'

  let extraContext = ''
  try {
    if (intent === 'comparison') {
      extraContext = await buildComparisonContext(message)
    } else if (intent === 'view_change') {
      extraContext = await buildViewChangeContext()
    } else if (intent === 'outcome') {
      extraContext = await buildOutcomeContext()
    }
  } catch {
    // 구조화 컨텍스트 실패는 무시 (벡터 컨텍스트만으로 진행)
  }

  // ── 벡터 검색 ─────────────────────────────────────────────────────────────
  let searchResults: Awaited<ReturnType<typeof searchKnowledge>> = []
  let sources: { title: string; url: string; issuer: string | null; published_at: string | null }[] = []

  try {
    const embedding = await embedQuery(message)
    searchResults = await searchKnowledge(embedding, { historical, limit: 8 })
    sources = searchResults
      .filter((r) => r.source_title)
      .map((r) => ({
        title: r.source_title ?? '',
        url: r.source_url ?? '',
        issuer: r.issuer,
        published_at: r.published_at,
      }))
      // dedupe by url
      .filter((s, i, arr) => arr.findIndex((x) => x.url === s.url) === i)
      .slice(0, 5)
  } catch {
    // 임베딩/검색 실패: 빈 컨텍스트로 진행
  }

  const vectorContext = searchResults.length
    ? formatSearchContext(searchResults)
    : '(현재 검색 가능한 리서치 없음)'

  const systemPrompt = [
    SYSTEM_BASE,
    historical ? '\n모드: 과거 뷰 조회 — 시점 가중 없이 관련성순으로 조회됩니다.' : '',
    '\n\n[지식베이스 컨텍스트]',
    vectorContext,
    extraContext ? `\n\n${extraContext}` : '',
  ]
    .filter(Boolean)
    .join('\n')

  // ── 스트리밍 응답 ─────────────────────────────────────────────────────────
  const stream = anthropic.messages.stream({
    model: 'claude-sonnet-4-6',
    max_tokens: 2048,
    system: systemPrompt,
    messages: [
      ...history.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content })),
      { role: 'user', content: message },
    ],
  })

  let fullText = ''

  const readable = new ReadableStream({
    async start(controller) {
      // session_id를 첫 청크로 전달
      controller.enqueue(enc({ type: 'session', session_id: sid }))

      try {
        for await (const event of stream) {
          if (
            event.type === 'content_block_delta' &&
            event.delta.type === 'text_delta'
          ) {
            fullText += event.delta.text
            controller.enqueue(enc({ type: 'text', content: event.delta.text }))
          }
        }

        // sources 전송
        if (sources.length) {
          controller.enqueue(enc({ type: 'sources', sources }))
        }
        controller.enqueue(enc({ type: 'done' }))

        // assistant 메시지 저장
        await db.insert(chat_messages).values({
          session_id: sid,
          role: 'assistant',
          content: fullText,
          sources: sources.length ? sources : null,
        })
      } catch (err) {
        controller.enqueue(enc({ type: 'error', message: String(err) }))
      } finally {
        controller.close()
      }
    },
  })

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
