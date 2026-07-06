'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

type QualityScores = {
  relevance?: number
  density?: number
  authority?: number
  novelty?: number
}

type Source = {
  id: string
  title: string
  url: string
  issuer: string
  published_at: string | null
  sector_tags: string[] | null
  quality: QualityScores | null
  gate_note: string | null
  claims_count: number
}

const REASON_TAGS = [
  { value: 'irrelevant', label: '섹터 무관' },
  { value: 'shallow', label: '분석 부족' },
  { value: 'duplicate', label: '중복' },
  { value: 'stale', label: '시효 만료' },
] as const

type ReasonTag = typeof REASON_TAGS[number]['value']

const SCORE_COLOR = (n: number) =>
  n >= 4 ? 'text-emerald-400' : n >= 3 ? 'text-yellow-400' : 'text-red-400'

export default function ReviewCard({ source }: { source: Source }) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [rejectMode, setRejectMode] = useState(false)
  const [reasonTag, setReasonTag] = useState<ReasonTag | ''>('')
  const [note, setNote] = useState('')

  const submit = async (decision: 'accept' | 'reject') => {
    if (decision === 'reject' && !reasonTag) return
    setLoading(true)
    await fetch(`/api/review/${source.id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, reason_tag: reasonTag || undefined, note: note || undefined }),
    })
    router.refresh()
  }

  const q = source.quality ?? {}
  const dims = ['relevance', 'density', 'authority', 'novelty'] as const

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-5 space-y-4">
      {/* 헤더 */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-white hover:text-blue-400 transition-colors line-clamp-2"
          >
            {source.title}
          </a>
          <p className="text-xs text-neutral-500 mt-1">
            {source.issuer} · {source.published_at ?? '날짜 없음'}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {source.sector_tags?.map((tag) => (
            <span key={tag} className="text-xs bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded">
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* 루브릭 점수 */}
      {source.quality && (
        <div className="grid grid-cols-4 gap-3">
          {dims.map((dim) => {
            const val = q[dim] ?? 0
            return (
              <div key={dim} className="text-center">
                <div className={`text-lg font-semibold tabular-nums ${SCORE_COLOR(val)}`}>{val}</div>
                <div className="text-xs text-neutral-600 mt-0.5">{dim}</div>
              </div>
            )
          })}
        </div>
      )}

      {/* claims 건수 + gate_note */}
      <div className="flex items-center gap-3 text-xs text-neutral-500">
        <span>claims {source.claims_count}건</span>
        {source.gate_note && (
          <span className="text-neutral-600 truncate">{source.gate_note}</span>
        )}
      </div>

      {/* 액션 */}
      {!rejectMode ? (
        <div className="flex gap-2 pt-1">
          <button
            onClick={() => submit('accept')}
            disabled={loading}
            className="flex-1 text-sm py-1.5 rounded bg-emerald-800 hover:bg-emerald-700 text-emerald-100 disabled:opacity-40 transition-colors"
          >
            승인
          </button>
          <button
            onClick={() => setRejectMode(true)}
            disabled={loading}
            className="flex-1 text-sm py-1.5 rounded bg-neutral-800 hover:bg-red-900 text-neutral-300 disabled:opacity-40 transition-colors"
          >
            반려
          </button>
        </div>
      ) : (
        <div className="space-y-3 pt-1">
          <div className="grid grid-cols-2 gap-2">
            {REASON_TAGS.map((t) => (
              <button
                key={t.value}
                onClick={() => setReasonTag(t.value)}
                className={`text-xs py-1.5 rounded border transition-colors ${
                  reasonTag === t.value
                    ? 'border-red-500 bg-red-900/30 text-red-300'
                    : 'border-neutral-700 text-neutral-400 hover:border-neutral-500'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="메모 (선택)"
            className="w-full text-xs bg-neutral-800 text-neutral-300 rounded px-3 py-2 resize-none h-16 border border-neutral-700 focus:outline-none focus:border-neutral-500"
          />
          <div className="flex gap-2">
            <button
              onClick={() => submit('reject')}
              disabled={loading || !reasonTag}
              className="flex-1 text-sm py-1.5 rounded bg-red-900 hover:bg-red-800 text-red-100 disabled:opacity-40 transition-colors"
            >
              반려 확정
            </button>
            <button
              onClick={() => setRejectMode(false)}
              className="text-sm px-4 py-1.5 rounded bg-neutral-800 text-neutral-400 hover:text-neutral-200 transition-colors"
            >
              취소
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
