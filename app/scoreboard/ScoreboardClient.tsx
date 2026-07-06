'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

type Outcome = 'hit' | 'miss' | 'partial' | 'open' | null

type Claim = {
  id: string
  issuer: string
  sector: string
  claim_ko: string
  direction: string | null
  horizon: string | null
  published_at: string
  outcome: Outcome
}

const OUTCOME_STYLES: Record<NonNullable<Outcome>, string> = {
  hit:     'bg-emerald-900/40 text-emerald-300 border-emerald-700',
  miss:    'bg-red-900/40 text-red-300 border-red-700',
  partial: 'bg-amber-900/40 text-amber-300 border-amber-700',
  open:    'bg-neutral-800 text-neutral-400 border-neutral-600',
}

const OUTCOME_LABEL: Record<NonNullable<Outcome>, string> = {
  hit: '적중',
  miss: '빗나감',
  partial: '부분적중',
  open: '진행중',
}

const DIR_COLOR: Record<string, string> = {
  bullish: 'text-emerald-400',
  bearish: 'text-red-400',
  neutral: 'text-neutral-400',
}

export default function ScoreboardClient({ claims }: { claims: Claim[] }) {
  const router = useRouter()
  const [updating, setUpdating] = useState<string | null>(null)

  const setOutcome = async (id: string, outcome: Outcome) => {
    setUpdating(id)
    await fetch(`/api/scoreboard/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ outcome }),
    })
    router.refresh()
    setUpdating(null)
  }

  return (
    <div className="space-y-2">
      {claims.map((c) => (
        <div
          key={c.id}
          className="bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-3 flex items-start gap-4"
        >
          {/* 왼쪽: claim 정보 */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-neutral-500 font-medium">{c.issuer}</span>
              <span className="text-neutral-700">·</span>
              <span className="text-xs text-neutral-600">{String(c.published_at).slice(0, 7)}</span>
              {c.direction && (
                <>
                  <span className="text-neutral-700">·</span>
                  <span className={`text-xs ${DIR_COLOR[c.direction] ?? 'text-neutral-400'}`}>
                    {c.direction}
                  </span>
                </>
              )}
              {c.horizon && (
                <span className="text-xs text-neutral-700">({c.horizon})</span>
              )}
            </div>
            <p className="text-sm text-neutral-300 leading-snug">{c.claim_ko}</p>
          </div>

          {/* 오른쪽: outcome 버튼 */}
          <div className="shrink-0 flex gap-1">
            {(['hit', 'miss', 'partial', 'open'] as const).map((o) => (
              <button
                key={o}
                onClick={() => setOutcome(c.id, c.outcome === o ? null : o)}
                disabled={updating === c.id}
                className={`text-xs px-2 py-1 rounded border transition-colors disabled:opacity-40 ${
                  c.outcome === o
                    ? OUTCOME_STYLES[o]
                    : 'border-neutral-800 text-neutral-600 hover:border-neutral-600 hover:text-neutral-400'
                }`}
              >
                {OUTCOME_LABEL[o]}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
