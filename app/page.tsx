import { db } from '@/lib/db'
import { sources, claims } from '@/db/schema'
import { eq, sql, inArray } from 'drizzle-orm'
import Link from 'next/link'
import { promises as fs } from 'fs'
import path from 'path'

const SECTORS = [
  {
    id: 'power_equipment',
    label: '전력기기',
    description: '변압기 · HVDC · ESS · 전력망 인프라',
    icon: '⚡',
  },
  {
    id: 'ai_semis',
    label: 'AI 반도체',
    description: 'GPU · HBM · CoWoS · AI 가속기 · 데이터센터',
    icon: '🔲',
  },
] as const

async function getSectorStats(sectorId: string) {
  const [claimCount] = await db
    .select({ count: sql<number>`count(*)` })
    .from(claims)
    .where(eq(claims.sector, sectorId))

  const wikiPath = path.join(process.cwd(), 'kb', 'wiki', `${sectorId}.md`)
  let updatedAt: string | null = null
  try {
    const raw = await fs.readFile(wikiPath, 'utf-8')
    const match = raw.match(/updated_at:\s*(.+)/)
    updatedAt = match?.[1]?.trim() ?? null
  } catch {
    // wiki not yet generated
  }

  return { claimCount: Number(claimCount.count), updatedAt }
}

async function getQueueCount() {
  const [row] = await db
    .select({ count: sql<number>`count(*)` })
    .from(sources)
    .where(eq(sources.status, 'queued'))
  return Number(row.count)
}

export default async function HomePage() {
  const [sectorStats, queueCount] = await Promise.all([
    Promise.all(SECTORS.map((s) => getSectorStats(s.id).then((stat) => ({ ...s, ...stat })))),
    getQueueCount(),
  ])

  return (
    <div className="max-w-3xl mx-auto px-6 py-14">
      <div className="mb-10">
        <h1 className="text-2xl font-semibold text-white">Research Wiki</h1>
        <p className="text-sm text-neutral-500 mt-2">
          글로벌 기관 리서치(IB·국제기구·컨설팅) 수집 → 지식화 → wiki/RAG 개인 도구
        </p>
      </div>

      {/* 섹터 카드 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
        {sectorStats.map((sector) => (
          <Link
            key={sector.id}
            href={`/wiki/${sector.id}`}
            className="group block bg-neutral-900 border border-neutral-800 rounded-lg p-5 hover:border-neutral-600 transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <span className="text-lg">{sector.icon}</span>
              {sector.claimCount > 0 && (
                <span className="text-xs text-neutral-600 bg-neutral-800 px-2 py-0.5 rounded-full">
                  {sector.claimCount}건
                </span>
              )}
            </div>
            <h2 className="text-sm font-semibold text-white group-hover:text-blue-400 transition-colors">
              {sector.label}
            </h2>
            <p className="text-xs text-neutral-600 mt-1">{sector.description}</p>
            {sector.updatedAt ? (
              <p className="text-xs text-neutral-700 mt-3">wiki 갱신: {sector.updatedAt}</p>
            ) : (
              <p className="text-xs text-neutral-800 mt-3">wiki 미생성</p>
            )}
          </Link>
        ))}
      </div>

      {/* 하단 링크 */}
      <div className="flex items-center gap-6 text-sm text-neutral-600">
        <Link
          href="/review"
          className="hover:text-neutral-300 transition-colors flex items-center gap-1.5"
        >
          검토 대기열
          {queueCount > 0 && (
            <span className="text-xs bg-amber-900/50 text-amber-400 px-1.5 py-0.5 rounded-full">
              {queueCount}
            </span>
          )}
        </Link>
        <span className="text-neutral-800">·</span>
        <span className="text-neutral-700 text-xs">HANDOVER.md 참조</span>
      </div>
    </div>
  )
}
