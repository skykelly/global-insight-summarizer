/**
 * lib/rag.ts — RAG 유틸리티 (pgvector 시점 가중 검색 + 질의 의도 감지)
 *
 * - time-decay: similarity × exp(-λ × days_old), λ = ln(2)/180 (반감기 180일)
 * - historical 모드: 감쇠 off
 * - 질의 의도 감지: comparison | view_change | outcome | historical | general
 * - 비교형 질의 시 claims 구조화 컨텍스트 주입
 */

import { db, pool } from '@/lib/db'
import { claims, sources } from '@/db/schema'
import { eq, and, inArray, sql } from 'drizzle-orm'
import { getOpenAI } from '@/lib/openai'
import { detectSectorHint } from '@/lib/taxonomy'

// ── 타입 ──────────────────────────────────────────────────────────────────────

export type QueryIntent = 'comparison' | 'view_change' | 'outcome' | 'historical' | 'general'

export type SearchResult = {
  content: string
  issuer: string | null
  published_at: string | null
  sector: string | null
  similarity: number
  score: number
  source_title?: string
  source_url?: string
}

// ── 임베딩 ────────────────────────────────────────────────────────────────────

export async function embedQuery(text: string): Promise<number[]> {
  const resp = await getOpenAI().embeddings.create({
    model: 'text-embedding-3-small',
    input: text.slice(0, 4000),
  })
  return resp.data[0].embedding
}

// ── 질의 의도 감지 ─────────────────────────────────────────────────────────────

const INTENT_PATTERNS: Record<Exclude<QueryIntent, 'general'>, RegExp[]> = {
  comparison: [/하우스별/i, /기관별/i, /누구는.*뭐라/i, /각\s*기관/i, /비교/i, /vs\.?\s/i, /견해 차이/i],
  view_change: [/뷰\s*변화/i, /기존\s*뷰/i, /달라졌/i, /변했/i, /수정(했|된)/i, /업데이트/i, /이전\s*전망/i],
  outcome: [/누가\s*맞/i, /적중/i, /outcome/i, /맞췄/i, /틀렸/i, /결과적으로/i, /실제로/i],
  historical: [/과거/i, /\d+개월\s*전/i, /작년/i, /당시/i, /예전/i, /(\d{4})년\s*\d+월/i],
}

export function detectIntent(query: string): QueryIntent {
  for (const [intent, patterns] of Object.entries(INTENT_PATTERNS)) {
    if (patterns.some((p) => p.test(query))) return intent as QueryIntent
  }
  return 'general'
}

// ── pgvector 시점 가중 검색 ───────────────────────────────────────────────────

// λ = ln(2)/180 ≈ 0.003856  반감기 180일
const LAMBDA = Math.LN2 / 180

export async function searchKnowledge(
  embedding: number[],
  opts: { historical?: boolean; limit?: number; sector?: string } = {},
): Promise<SearchResult[]> {
  const { historical = false, limit = 8, sector } = opts

  const embeddingStr = JSON.stringify(embedding)
  const decayExpr = historical
    ? `(1 - (ke.embedding <=> '${embeddingStr}'::vector))`
    : `(1 - (ke.embedding <=> '${embeddingStr}'::vector)) * EXP(-${LAMBDA.toFixed(6)} * GREATEST(0, EXTRACT(EPOCH FROM (NOW() - ki.published_at::timestamptz)) / 86400))`

  const sectorFilter = sector ? `AND ki.sector = '${sector.replace(/'/g, "''")}'` : ''

  const { rows } = await pool.query<{
    content: string
    issuer: string
    published_at: string
    sector: string
    source_title: string
    source_url: string
    similarity: number
    score: number
  }>(`
    SELECT
      ke.content,
      ki.issuer,
      ki.published_at::text,
      ki.sector,
      s.title  AS source_title,
      s.url    AS source_url,
      (1 - (ke.embedding <=> '${embeddingStr}'::vector))::float AS similarity,
      (${decayExpr})::float AS score
    FROM knowledge_embeddings ke
    JOIN knowledge_items ki ON ki.id = ke.ref_id
    JOIN sources s ON s.id = ki.source_id
    WHERE ke.embedding IS NOT NULL
      ${sectorFilter}
    ORDER BY score DESC
    LIMIT ${limit}
  `)

  return rows
}

// ── 구조화 컨텍스트 빌더 ──────────────────────────────────────────────────────

export async function buildComparisonContext(query: string): Promise<string> {
  // 질의에서 섹터 힌트 추출 (configs/taxonomy.yaml 기준 — 하드코딩 금지)
  const sectorHint = detectSectorHint(query)

  const rows = await db
    .select({
      issuer: claims.issuer,
      sector: claims.sector,
      claim_ko: claims.claim_ko,
      direction: claims.direction,
      horizon: claims.horizon,
      published_at: claims.published_at,
      metrics: claims.metrics,
    })
    .from(claims)
    .innerJoin(sources, eq(sources.id, claims.source_id))
    .where(
      and(
        inArray(sources.status, ['auto_accepted', 'accepted']),
        sectorHint ? eq(claims.sector, sectorHint) : undefined,
      ),
    )
    .orderBy(claims.published_at)
    .limit(40)

  if (!rows.length) return ''

  // 이슈어별 그룹화
  const grouped = new Map<string, typeof rows>()
  for (const r of rows) {
    const key = r.issuer
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(r)
  }

  const lines = ['## 기관별 뷰 비교']
  for (const [issuer, items] of grouped) {
    lines.push(`\n### ${issuer}`)
    for (const c of items.slice(0, 3)) {
      const pub = String(c.published_at).slice(0, 7)
      const dir = c.direction ?? 'neutral'
      const hz = c.horizon ? ` (${c.horizon})` : ''
      lines.push(`- [${pub}] ${dir}${hz}: ${c.claim_ko}`)
    }
  }
  return lines.join('\n')
}

export async function buildViewChangeContext(): Promise<string> {
  const { rows } = await pool.query<{
    issuer: string
    sector: string
    claim_ko: string
    direction: string
    published_at: string
    prev_claim_ko: string
    prev_direction: string
    prev_published_at: string
  }>(`
    SELECT
      c.issuer, c.sector, c.claim_ko, c.direction, c.published_at::text,
      prev.claim_ko  AS prev_claim_ko,
      prev.direction AS prev_direction,
      prev.published_at::text AS prev_published_at
    FROM claims c
    JOIN claims prev ON prev.id = c.supersedes
    JOIN sources s ON s.id = c.source_id
    WHERE c.supersedes IS NOT NULL
      AND s.status IN ('auto_accepted', 'accepted')
    ORDER BY c.published_at DESC
    LIMIT 20
  `)

  if (!rows.length) return ''

  const lines = ['## 뷰 변화 이력']
  for (const r of rows) {
    const pub = r.published_at.slice(0, 7)
    const prevPub = r.prev_published_at.slice(0, 7)
    lines.push(
      `- **[${r.issuer}, ${pub}]** ${r.prev_direction ?? '?'} → ${r.direction ?? '?'}: ${r.claim_ko}`,
      `  _(이전 뷰 [${r.issuer}, ${prevPub}]: ${r.prev_claim_ko})_`,
    )
  }
  return lines.join('\n')
}

export async function buildOutcomeContext(): Promise<string> {
  const rows = await db
    .select({
      issuer: claims.issuer,
      sector: claims.sector,
      claim_ko: claims.claim_ko,
      direction: claims.direction,
      published_at: claims.published_at,
      outcome: claims.outcome,
    })
    .from(claims)
    .innerJoin(sources, eq(sources.id, claims.source_id))
    .where(
      and(
        inArray(sources.status, ['auto_accepted', 'accepted']),
        sql`${claims.outcome} IS NOT NULL`,
      ),
    )
    .orderBy(claims.published_at)
    .limit(30)

  if (!rows.length) return ''

  const lines = ['## 전망 적중률 현황']
  for (const r of rows) {
    const pub = String(r.published_at).slice(0, 7)
    lines.push(`- [${r.issuer}, ${pub}] ${r.outcome?.toUpperCase()}: ${r.claim_ko}`)
  }
  return lines.join('\n')
}

// ── 컨텍스트 포맷팅 ──────────────────────────────────────────────────────────

export function formatSearchContext(results: SearchResult[]): string {
  return results
    .map((r) => {
      const pub = r.published_at ? r.published_at.slice(0, 7) : '날짜불명'
      const issuer = r.issuer ?? '발행처불명'
      const sector = r.sector ?? ''
      return `[${issuer}, ${pub}${sector ? ', ' + sector : ''}]\n${r.content}`
    })
    .join('\n\n---\n\n')
}
