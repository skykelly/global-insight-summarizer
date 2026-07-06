import { db } from '@/lib/db'
import { claims, sources } from '@/db/schema'
import { eq, inArray, sql } from 'drizzle-orm'
import ScoreboardClient from './ScoreboardClient'
import Link from 'next/link'

export const dynamic = 'force-dynamic'
export const metadata = { title: 'Research Wiki — Scoreboard' }

const SECTORS = ['power_equipment', 'ai_semis'] as const
const OUTCOMES = ['hit', 'miss', 'partial', 'open'] as const

const SECTOR_LABEL: Record<string, string> = {
  power_equipment: '전력기기',
  ai_semis: 'AI 반도체',
}
const OUTCOME_LABEL: Record<string, string> = {
  hit: '적중',
  miss: '빗나감',
  partial: '부분',
  open: '진행중',
}
const OUTCOME_COLOR: Record<string, string> = {
  hit: 'text-emerald-400',
  miss: 'text-red-400',
  partial: 'text-amber-400',
  open: 'text-neutral-500',
}

export default async function ScoreboardPage() {
  // ── 1. aggregate: issuer × sector × outcome 집계 ─────────────────────────
  const aggRows = await db
    .select({
      issuer: claims.issuer,
      sector: claims.sector,
      outcome: claims.outcome,
      count: sql<number>`count(*)`,
    })
    .from(claims)
    .innerJoin(sources, eq(sources.id, claims.source_id))
    .where(inArray(sources.status, ['auto_accepted', 'accepted']))
    .groupBy(claims.issuer, claims.sector, claims.outcome)
    .orderBy(claims.issuer, claims.sector)

  // ── 2. 집계 테이블 구조 ─────────────────────────────────────────────────────
  type AggKey = `${string}|${string}`
  const agg = new Map<AggKey, Record<string, number>>()

  for (const row of aggRows) {
    const key: AggKey = `${row.issuer}|${row.sector}`
    if (!agg.has(key)) agg.set(key, {})
    const o = row.outcome ?? 'open'
    agg.get(key)![o] = (agg.get(key)![o] ?? 0) + Number(row.count)
  }

  // ── 3. 전체 claims 목록 (판정 UI용) ─────────────────────────────────────────
  const allClaims = await db
    .select({
      id: claims.id,
      issuer: claims.issuer,
      sector: claims.sector,
      claim_ko: claims.claim_ko,
      direction: claims.direction,
      horizon: claims.horizon,
      published_at: claims.published_at,
      outcome: claims.outcome,
    })
    .from(claims)
    .innerJoin(sources, eq(sources.id, claims.source_id))
    .where(inArray(sources.status, ['auto_accepted', 'accepted']))
    .orderBy(claims.published_at)

  const claimsBySector = Object.fromEntries(
    SECTORS.map((s) => [s, allClaims.filter((c) => c.sector === s)]),
  ) as Record<string, typeof allClaims>

  // ── 집계 요약 ────────────────────────────────────────────────────────────────
  const totalJudged = allClaims.filter((c) => c.outcome && c.outcome !== 'open').length
  const totalHit = allClaims.filter((c) => c.outcome === 'hit').length
  const hitRate = totalJudged ? Math.round((totalHit / totalJudged) * 100) : null

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex items-center gap-3 mb-8">
        <Link href="/" className="text-xs text-neutral-600 hover:text-neutral-400 transition-colors">
          ← Research Wiki
        </Link>
        <span className="text-neutral-700">/</span>
        <h1 className="text-xl font-semibold text-white">Scoreboard</h1>
        {hitRate !== null && (
          <span className="ml-auto text-xs text-neutral-500">
            판정 완료 {totalJudged}건 · 적중률{' '}
            <span className="text-emerald-400 font-medium">{hitRate}%</span>
          </span>
        )}
      </div>

      {/* ── 집계 테이블 ───────────────────────────────────────────────────── */}
      {agg.size > 0 && (
        <div className="mb-10 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="text-left py-2 pr-4 text-neutral-500 font-medium">발행처</th>
                <th className="text-left py-2 pr-4 text-neutral-500 font-medium">섹터</th>
                {OUTCOMES.map((o) => (
                  <th key={o} className={`text-center py-2 px-3 font-medium ${OUTCOME_COLOR[o]}`}>
                    {OUTCOME_LABEL[o]}
                  </th>
                ))}
                <th className="text-center py-2 px-3 text-neutral-500 font-medium">합계</th>
              </tr>
            </thead>
            <tbody>
              {Array.from(agg.entries()).map(([key, counts]) => {
                const [issuer, sector] = key.split('|')
                const total = Object.values(counts).reduce((a, b) => a + b, 0)
                return (
                  <tr key={key} className="border-b border-neutral-900 hover:bg-neutral-900/50">
                    <td className="py-2 pr-4 text-neutral-300">{issuer}</td>
                    <td className="py-2 pr-4 text-neutral-500">
                      {SECTOR_LABEL[sector] ?? sector}
                    </td>
                    {OUTCOMES.map((o) => (
                      <td key={o} className={`text-center py-2 px-3 tabular-nums ${OUTCOME_COLOR[o]}`}>
                        {counts[o] ?? 0}
                      </td>
                    ))}
                    <td className="text-center py-2 px-3 text-neutral-500 tabular-nums">{total}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* ── 섹터별 claim 목록 + 수동 판정 ──────────────────────────────── */}
      {allClaims.length === 0 ? (
        <p className="text-sm text-neutral-600 py-12 text-center">
          판정 가능한 claims가 없습니다. 지식 파이프라인 실행 후 이 페이지를 확인하세요.
        </p>
      ) : (
        SECTORS.map((sector) => {
          const sectorClaims = claimsBySector[sector]
          if (!sectorClaims?.length) return null
          return (
            <section key={sector} className="mb-10">
              <h2 className="text-sm font-semibold text-neutral-400 mb-3">
                {SECTOR_LABEL[sector]} ({sectorClaims.length}건)
              </h2>
              <ScoreboardClient
                claims={sectorClaims.map((c) => ({
                  ...c,
                  outcome: (c.outcome as 'hit' | 'miss' | 'partial' | 'open' | null) ?? null,
                  published_at: String(c.published_at),
                }))}
              />
            </section>
          )
        })
      )}
    </div>
  )
}
